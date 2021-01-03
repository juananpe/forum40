from contextlib import contextmanager

import psycopg2
from psycopg2.pool import ThreadedConnectionPool

# PostgSQL
from config.settings import PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD

postgres_con = psycopg2.connect(host=PG_HOST, port=PG_PORT, database=PG_DATABASE, user=PG_USER, password=PG_PASSWORD)

db_pool = ThreadedConnectionPool(10, 50, host=PG_HOST, port=PG_PORT, database=PG_DATABASE, user=PG_USER, password=PG_PASSWORD)


# TODO: Remove
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
