from flask_pymongo import PyMongo
import psycopg2
from psycopg2.extras import RealDictCursor

## Mongo DB
mongo = PyMongo()

## PostgSQL
PG_HOST = 'postgres'
PG_PORT = 5432
PG_DATABASE = 'omp'
PG_USER = 'postgres'
PG_PASSWORD = 'postgres'

con = psycopg2.connect(host=PG_HOST, port=PG_PORT, database=PG_DATABASE, user=PG_USER, password=PG_PASSWORD)
postgres = con.cursor()