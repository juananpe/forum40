from flask_pymongo import PyMongo
import psycopg2
from psycopg2.extras import RealDictCursor

## Mongo DB
mongo = PyMongo()

## PostgSQL
PG_HOST = 'postgres'
PG_PORT = 5432
PG_DATABASE = 'omp'
PG_USER = 'postgres' # TODO hide
PG_PASSWORD = 'postgres' # TODO hide

postgres_con = psycopg2.connect(host=PG_HOST, port=PG_PORT, database=PG_DATABASE, user=PG_USER, password=PG_PASSWORD)
import sys
print(postgres_con, file=sys.stdout)
postgres = postgres_con.cursor()
postgres_json = postgres_con.cursor(cursor_factory=RealDictCursor)
