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
use redis::{Commands, Connection, RedisError};
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

#[derive(RustcDecodable, RustcEncodable)]
struct DownloadSubmission {
    uuid: String,
    mod_str: String,
}

#[derive(Clone, Copy, Debug)]
enum Rating {
    Poor,
    BelowAverage,
    Average,
    AboveAverage,
    Excellent,
}

impl From<usize> for Rating {
    fn from(rating: usize) -> Self {
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
        let r = try!(d.read_usize());
        Ok(Rating::from(r))
    }
}

impl Encodable for Rating {
    fn encode<S: Encoder>(&self, s: &mut S) -> Result<(), S::Error> {
        let as_usize = *self as usize;
        s.emit_usize(as_usize)
    }
}

#[derive(RustcEncodable)]
struct StatsResults {
    average_ratings: HashMap<String, Rating>,
    amount_ratings: HashMap<String, usize>,
    own_ratings: Option<HashMap<String, Rating>>,
    downloads: HashMap<String, usize>,
}

fn incr_requests(conn: &Connection) {
    if let Err(_) = conn.incr::<_, _, usize>("requests", 1) {
        println!("failed to incr request counter.")
    }
}

fn get_mod_rating(conn: &Connection, mod_str: &str) -> Result<(Rating, usize), RedisError> {
    let ratings = try!(conn.hvals::<_, Vec<usize>>(format!("{}_ratings", mod_str)));
    let length = ratings.len();
    let mut sum = 0;
    for rating in ratings {
        sum += rating;
    }
    match length {
        0 => Ok((Rating::Poor, length)),
        _ => Ok((Rating::from(sum / length), length)),
    }
}

fn get_mod_downloads(conn: &Connection, mod_str: &str) -> Result<usize, RedisError> {
    let downloads = try!(conn.hvals::<_, Vec<usize>>(format!("{}_downloads", mod_str)));
    Ok(downloads.iter().fold(0, |acc, &x| acc + x))
}


const OK_RESP: (StatusCode, &'static str) = (StatusCode::Ok, "ok");

fn main() {
    let mut webserver = Nickel::new();

    let redis_url = env::var("DATABASE_URL").unwrap_or("redis://localhost/3".to_owned());
    println!("connecting to redis @ {}", redis_url);

    let redispool = RedisMiddleware::new(&*redis_url, 3, Box::new(NopErrorHandler)).unwrap();
    webserver.utilize(redispool);

    webserver.post("/submit_rating",
                   middleware! { |request, response|
        let rcn_ref = request.redis_conn();
        let redis_conn = rcn_ref.deref();
        incr_requests(redis_conn);
        let sbm = try_with!(response, {
            request.json_as::<RatingSubmission>().map_err(|e| (StatusCode::BadRequest, e))
        });
        println!("{} rates {} as {:?}", sbm.uuid, sbm.mod_str, sbm.rating);
        let _: bool = try_with!(response, {
            redis_conn.hset("mods", &*sbm.mod_str, true).map_err(|e| (StatusCode::BadRequest, e))
        });
        let _: usize = try_with!(response, {
            let key = format!("{}_ratings", sbm.mod_str);
            redis_conn.hset(key, sbm.uuid, sbm.rating as usize).map_err(|e|
                (StatusCode::BadRequest, e)
            )
        });
        OK_RESP
    });

    webserver.get("/rating/:mod",
                  middleware! { |request, response|
        let rcn_ref = request.redis_conn();
        let redis_conn = rcn_ref.deref();
        incr_requests(redis_conn);
        let mod_str = request.param("mod").unwrap();
        let result = try_with!(response, {
            get_mod_rating(redis_conn, mod_str).map_err(|e| (StatusCode::BadRequest, e))
        });
        match result {
            (_, 0) => (StatusCode::NotFound, "Not Found!".to_owned()),
            (rating, sbm) => (StatusCode::Ok, format!("{:?}, {} submissions", rating, sbm)),
        }
    });

    webserver.get("/stats",
                  middleware! { |request, mut response|
        let rcn_ref = request.redis_conn();
        let redis_conn = rcn_ref.deref();
        incr_requests(&redis_conn);

        let mods = try_with!(response, {
            redis_conn.hkeys::<_, Vec<String>>("mods").map_err(|e| (StatusCode::BadRequest, e))
        });

        let mut own_ratings: HashMap<String, Rating> = HashMap::new();
        let mut amount_ratings: HashMap<String, usize> = HashMap::new();
        let mut average_ratings: HashMap<String, Rating> = HashMap::new();
        let mut mod_downloads: HashMap<String, usize> = HashMap::new();

        for mod_str in mods {
            let mod_str = mod_str.as_str();

            let downloads = try_with!(response, {
                get_mod_downloads(redis_conn, mod_str).map_err(|e| (StatusCode::BadRequest, e))
            });
            mod_downloads.insert(mod_str.to_owned(), downloads);

            let (rating, sbm) = try_with!(response, {
                get_mod_rating(redis_conn, mod_str).map_err(|e| (StatusCode::BadRequest, e))
            });
            if sbm == 0 {
                continue;
            }
            average_ratings.insert(mod_str.to_owned(), rating);
            amount_ratings.insert(mod_str.to_owned(), sbm);
            if let Some(uuid) = request.query().get("uuid") {
                if let Ok(rating) = redis_conn.hget::<_, _, usize>(mod_str, uuid) {
                    own_ratings.insert(mod_str.to_owned(), Rating::from(rating));
                }
            }
        }

        let result = StatsResults {
            average_ratings: average_ratings,
            amount_ratings: amount_ratings,
            own_ratings: match request.query().get("uuid") {
                Some(_) => Some(own_ratings),
                None => None,
            },
            downloads: mod_downloads,
        };
        response.set(MediaType::Json);
        json::encode(&result).unwrap()
    });

    webserver.post("/submit_download",
                   middleware! { |request, response|
        let rcn_ref = request.redis_conn();
        let redis_conn = rcn_ref.deref();
        incr_requests(redis_conn);
        let sbm = try_with!(response, {
            request.json_as::<DownloadSubmission>().map_err(|e| (StatusCode::BadRequest, e))
        });
        println!("{} downloaded {}", sbm.uuid, sbm.mod_str);
        let _: bool = try_with!(response, {
            redis_conn.hset("mods", &*sbm.mod_str, true).map_err(|e| (StatusCode::BadRequest, e))
        });
        let _: usize = try_with!(response, {
            redis_conn.hincr(format!("{}_downloads", sbm.mod_str), sbm.uuid, 1).map_err(|e|
                (StatusCode::BadRequest, e)
            )
        });
        OK_RESP
    });

    webserver.listen("127.0.0.1:7998")
}
