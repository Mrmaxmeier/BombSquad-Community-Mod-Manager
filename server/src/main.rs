extern crate rustc_serialize;
#[macro_use]
extern crate nickel;
extern crate redis;
extern crate r2d2;
extern crate r2d2_redis;
extern crate plugin;
extern crate typemap;

extern crate core;

use std::env;
use std::collections::HashMap;
use r2d2::NopErrorHandler;
use nickel::{Nickel, HttpRouter, JsonBody, MediaType, QueryString};
use nickel::status::StatusCode;
use core::ops::Deref;
use redis::{Commands, Connection};
use rustc_serialize::{Decodable, Decoder, Encodable, Encoder};
use rustc_serialize::json;

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


#[derive(RustcEncodable)]
struct RatingResults {
    average: HashMap<String, Rating>,
    own: Option<HashMap<String, Rating>>,
}

impl From<u8> for Rating {
    fn from(rating: u8) -> Self {
        match rating {
            0 => Rating::Poor,
            1 => Rating::BelowAverage,
            2 => Rating::Average,
            3 => Rating::AboveAverage,
            _ => Rating::Excellent,
        }
    }
}

impl Decodable for Rating {
    fn decode<D: Decoder>(d: &mut D) -> Result<Rating, D::Error> {
        let r = try!(d.read_u8());
        Ok(Rating::from(r))
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

    webserver.post("/submit",
                   middleware! { |request, response|
        let rcn_ref = request.redis_conn();
        let redis_conn = rcn_ref.deref();
        incr_requests(&redis_conn);
        let sbm = try_with!(response, {
            request.json_as::<RatingSubmission>().map_err(|e| (StatusCode::BadRequest, e))
        });
        println!("{} rates {} as {:?}", sbm.uuid, sbm.mod_str, sbm.rating);
        let _: u8 = try_with!(response, {
            redis_conn.hset(sbm.mod_str, sbm.uuid, sbm.rating as u8).map_err(|e|
                (StatusCode::BadRequest, e)
            )
        });
        OK_RESP
    });

    webserver.get("/rating/:mod",
                  middleware! { |request, response|
        let rcn_ref = request.redis_conn();
        let redis_conn = rcn_ref.deref();
        incr_requests(&redis_conn);
        let mod_str = request.param("mod").unwrap();
        let ratings = try_with!(response, {
            redis_conn.hvals::<_, Vec<u8>>(mod_str).map_err(|e| (StatusCode::BadRequest, e))
        });
        let length = ratings.len();
        let mut sum = 0usize;
        for rating in ratings {
            sum += rating as usize;
        }
        match length {
            0 => (StatusCode::NotFound, "{\"not_found\": true}".to_owned()),
            _ => (StatusCode::Ok, format!("{}", sum / length)),
        }
    });

    webserver.get("/ratings",
                  middleware! { |request, mut response|
        let rcn_ref = request.redis_conn();
        let redis_conn = rcn_ref.deref();
        incr_requests(&redis_conn);

        let mods = try_with!(response, {
            redis_conn.hkeys::<_, Vec<String>>("mods").map_err(|e| (StatusCode::BadRequest, e))
        });

        let mut own_ratings = HashMap::new();
        let mut average_ratings = HashMap::new();

        for mod_str in mods {
            let mod_str = mod_str.as_str();
            let ratings = try_with!(response, {
                redis_conn.hvals::<_, Vec<u8>>(mod_str).map_err(|e| (StatusCode::BadRequest, e))
            });
            let length = ratings.len();
            let mut sum = 0usize;
            for rating in ratings {
                sum += rating as usize;
            }
            if length > 0 {
                average_ratings.insert(mod_str.to_owned(), Rating::from((sum / length) as u8));
            }
            if let Some(uuid) = request.query().get("uuid") {
                if let Ok(rating) = redis_conn.hget::<_, _, u8>(mod_str, uuid) {
                    own_ratings.insert(mod_str.to_owned(), Rating::from(rating));
                }
            }
        }

        let result = RatingResults {
            average: average_ratings,
            own: match request.query().get("uuid") {
                Some(_) => Some(own_ratings),
                None => None,
            },
        };
        response.set(MediaType::Json);
        json::encode(&result).unwrap()
    });

    webserver.listen("127.0.0.1:7998")
}
