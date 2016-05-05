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
use redis::Commands;

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

//const REDIS_CONN_STRING: &'static str = "redis://[:<passwd>@]<hostname>[:port][/<db>]";
const REDIS_CONN_STRING: &'static str = "redis://localhost/db3";
//const REDIS_CONN_STRING: &'static str = "redis://127.0.0.1";
// "redis://127.0.0.1"

fn open_redis_conn() -> redis::RedisResult<redis::Connection> {
	let client = try!(redis::Client::open(REDIS_CONN_STRING));
	let con = try!(client.get_connection());
	Ok(con)
}

fn main() {
	let mut webserver = Nickel::new();

	let redis_conn = open_redis_conn().unwrap();

	let redis_url = env::var("DATABASE_URL").unwrap();
	let redispool = RedisMiddleware::new(&*redis_url,
										5,
										Box::new(NopErrorHandler)).unwrap();

	webserver.utilize(redispool);
	webserver.post("/submit", middleware! { |request, response|
		redis_conn.hset("mod", "uuid", Rating::Poor as u8);
		let test = request.json_as::<RatingSubmission>().unwrap();
		println!("{}", test.uuid);
		format!("deine mudd {} {}", 3, 4)
	});
	webserver.get("/rating/:mod", middleware! { |request|
		let _connection = request.redis_conn();
		redis_conn.incr("requests", 1);
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
