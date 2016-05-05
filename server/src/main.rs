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
use redis::{Commands, RedisError};

use redis_middleware::{RedisMiddleware, RedisRequestExtensions};
mod redis_middleware;

#[derive(RustcDecodable, RustcEncodable)]
struct RatingSubmission {
	uuid: String,
	mod_str: String,
	rating: u8,
}

enum Rating {
	Poor = 0,
	BelowAverage,
	Average,
	AboveAverage,
	Excellent,
}

fn main() {
	let mut webserver = Nickel::new();

	let redis_url = env::var("DATABASE_URL").unwrap_or("redis://localhost/3".to_owned());
	let redispool = RedisMiddleware::new(&*redis_url,
										5,
										Box::new(NopErrorHandler)).unwrap();

	webserver.utilize(redispool);
	webserver.post("/submit", middleware! { |request|
		let _redis_conn = request.redis_conn();
		let redis_conn = _redis_conn.deref();
		let test = request.json_as::<RatingSubmission>().unwrap();
		println!("{}", test.uuid);
		let r: Result<u8, RedisError> = redis_conn.hset("mod", "uuid", Rating::Poor as u8);
		match r {
			Err(_) => (StatusCode::NotFound, "{\"not_found\": true}"),
			Ok(_) => (StatusCode::Ok, "ok"),
		}
	});
	webserver.get("/rating/:mod", middleware! { |request|
		let _redis_conn = request.redis_conn();
		let redis_conn = _redis_conn.deref();
		let r: Result<u8, RedisError> = redis_conn.incr("requests", 1);
		match request.param("mod") {
			Some("test") => (StatusCode::Ok, "ok"),
			_ => (StatusCode::NotFound, "{\"not_found\": true}"),
		}
	});
	webserver.get("/ratings", middleware! { |request, response|
		format!("{{\"mod\": {}}}", 3)
	});

	webserver.listen("127.0.0.1:8080")
}
