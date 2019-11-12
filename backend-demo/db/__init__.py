from flask_pymongo import PyMongo
import psycopg2

## Mongo DB
mongo = PyMongo() # TODO remove offlang service

## PostgSQL
PG_HOST = 'postgres'
PG_PORT = 5432
PG_DATABASE = 'omp'
PG_USER = 'postgres' # TODO hide
PG_PASSWORD = 'postgres' # TODO hide

postgres_con = psycopg2.connect(host=PG_HOST, port=PG_PORT, database=PG_DATABASE, user=PG_USER, password=PG_PASSWORD)
