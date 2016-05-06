extern crate rustc_serialize;
#[macro_use] extern crate nickel;
extern crate redis;
extern crate r2d2;
extern crate r2d2_redis;
extern crate plugin;
extern crate typemap;

extern crate core;

use std::env;
use r2d2::NopErrorHandler;
use nickel::{Nickel, HttpRouter, JsonBody};
use nickel::status::StatusCode;
use core::ops::Deref;
use redis::{Commands, Connection};
use rustc_serialize::{Decodable, Decoder, Encodable, Encoder};

use redis_middleware::{RedisMiddleware, RedisRequestExtensions};
mod redis_middleware;

#[derive(RustcDecodable, RustcEncodable)]
struct RatingSubmission {
	uuid: String,
	mod_str: String,
	rating: Rating,
}

#[derive(Clone, Copy, Debug)]
enum Rating {
	Poor = 0,
	BelowAverage,
	Average,
	AboveAverage,
	Excellent,
}

impl Decodable for Rating {
	fn decode<D: Decoder>(d: &mut D) -> Result<Rating, D::Error> {
		let r = try!(d.read_u8());
		Ok(match r {
			0 => Rating::Poor,
			1 => Rating::BelowAverage,
			2 => Rating::Average,
			3 => Rating::AboveAverage,
			_ => Rating::Excellent,
		})
	}
}

impl Encodable for Rating {
	fn encode<S: Encoder>(&self, s: &mut S) -> Result<(), S::Error> {
		let as_u8 = *self as u8;
		s.emit_u8(as_u8)
	}
}

fn incr_requests(conn: &Connection) {
	if let Err(_) = conn.incr::<_, _, u64>("requests", 1) {
		println!("failed to incr request counter.")
	}
}

const OK_RESP: (StatusCode, &'static str) = (StatusCode::Ok, "ok");

fn main() {
	let mut webserver = Nickel::new();

	let redis_url = env::var("DATABASE_URL").unwrap_or("redis://localhost/3".to_owned());
	println!("connecting to redis @ {}", redis_url);

	let redispool = RedisMiddleware::new(&*redis_url, 3, Box::new(NopErrorHandler)).unwrap();
	webserver.utilize(redispool);

	webserver.post("/submit", middleware! { |request, response|
		let _redis_conn = request.redis_conn();
		let redis_conn = _redis_conn.deref();
		incr_requests(&redis_conn);
		let submission = try_with!(response, {
			request.json_as::<RatingSubmission>().map_err(|e| (StatusCode::BadRequest, e))
		});
		println!("{} rates {} as {:?}", submission.uuid, submission.mod_str, submission.rating);
		let r = redis_conn.hset::<_, _, _, u8>(submission.mod_str, submission.uuid, submission.rating as u8);
		match r {
			Err(_) => (StatusCode::NotFound, "{\"not_found\": true}"),
			Ok(_) => OK_RESP,
		}
	});

	webserver.get("/rating/:mod", middleware! { |request, response|
		let _redis_conn = request.redis_conn();
		let redis_conn = _redis_conn.deref();
		incr_requests(&redis_conn);
		let mod_str = request.param("mod").unwrap();
		let ratings = try_with!(response, {
			redis_conn.hvals::<_, Vec<u8>>(mod_str).map_err(|e| (StatusCode::BadRequest, e))
		});
		let length = ratings.len();
		let mut avg = 0usize;
		for rating in ratings {
			avg += rating as usize;
		}
		match length {
			0 => (StatusCode::NotFound, "{\"not_found\": true}".to_owned()),
			_ => (StatusCode::Ok, format!("{}", avg / length)),
		}
	});

	webserver.get("/ratings", middleware! { |request, response|
		format!("{{\"mod\": {}}}", 3)
	});

	webserver.listen("127.0.0.1:7998")
}
