
use std::sync::Arc;
use std::error::Error as StdError;

use nickel::{Request, Response, Middleware, Continue, MiddlewareResult};
use r2d2_redis::RedisConnectionManager;
use r2d2::{Pool, HandleError, Config, PooledConnection};
use typemap::Key;
use plugin::{Pluggable, Extensible};

pub struct RedisMiddleware {
    pub pool: Arc<Pool<RedisConnectionManager>>,
}

impl RedisMiddleware {
    pub fn new(connect_str: &str,
               num_connections: u32,
               error_handler: Box<HandleError<::r2d2_redis::Error>>)
               -> Result<RedisMiddleware, Box<StdError>> {
        let manager = try!(RedisConnectionManager::new(connect_str));

        let config = Config::builder()
                         .pool_size(num_connections)
                         .error_handler(error_handler)
                         .build();

        let pool = try!(Pool::new(config, manager));

        Ok(RedisMiddleware { pool: Arc::new(pool) })
    }
}

impl Key for RedisMiddleware {
    type Value = Arc<Pool<RedisConnectionManager>>;
}

impl<D> Middleware<D> for RedisMiddleware {
    fn invoke<'mw, 'conn>(&self,
                          req: &mut Request<'mw, 'conn, D>,
                          res: Response<'mw, D>)
                          -> MiddlewareResult<'mw, D> {
        req.extensions_mut().insert::<RedisMiddleware>(self.pool.clone());
        Ok(Continue(res))
    }
}

pub trait RedisRequestExtensions {
    fn redis_conn(&self) -> PooledConnection<RedisConnectionManager>;
}

impl<'a, 'b, D> RedisRequestExtensions for Request<'a, 'b, D> {
    fn redis_conn(&self) -> PooledConnection<RedisConnectionManager> {
        self.extensions().get::<RedisMiddleware>().unwrap().get().unwrap()
    }
}
