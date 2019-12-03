from flask_pymongo import PyMongo
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from contextlib import contextmanager

## Mongo DB
mongo = PyMongo() # TODO remove offlang service


## PostgSQL
PG_HOST = 'postgres'
PG_PORT = 5432
PG_DATABASE = 'omp'
PG_USER = 'postgres' # TODO hide
PG_PASSWORD = 'postgres' # TODO hide

postgres_con = psycopg2.connect(host=PG_HOST, port=PG_PORT, database=PG_DATABASE, user=PG_USER, password=PG_PASSWORD)

db_pool = ThreadedConnectionPool(10, 50, host=PG_HOST, port=PG_PORT, database=PG_DATABASE, user=PG_USER, password=PG_PASSWORD)

@contextmanager
def db_cursor(cursor_factory=None):
    conn = db_pool.getconn()
    try:
        if cursor_factory:
            with conn.cursor(cursor_factory=cursor_factory) as cur:
                yield cur
                conn.commit()
        else:
            with conn.cursor() as cur:
                yield cur
                conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        db_pool.putconn(conn)