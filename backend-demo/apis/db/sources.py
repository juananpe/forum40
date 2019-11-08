from flask import request
from flask_restplus import Resource, reqparse, fields
from apis.db import api

from db import postgres_con
from db.queries import COUNT_SOURCES
from models.db_models import source_parser
from psycopg2 import DatabaseError
from psycopg2.extras import RealDictCursor

ns = api.namespace('sources', description="sources api")


@ns.route('/')
class Sources(Resource):

    def get(self):
        query = "select * from sources"
        postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
        try:
            postgres.execute(query)
            postgres_con.commit()

        except DatabaseError:
            postgres_con.rollback()
            return {'msg': 'DatabaseError: transaction is aborted'}, 400

        sources = postgres.fetchall()
        return sources, 200

    @api.expect(source_parser)
    def post(self):
        args = source_parser.parse_args()
        name = args['name']
        domain = args['domain']
        postgres = postgres_con.cursor()
        insert_query = "INSERT INTO sources (name, domain) VALUES (%s, %s) RETURNING id;"

        try:
            postgres.execute(insert_query, (name, domain))
            postgres_con.commit()

        except DatabaseError:
            postgres_con.rollback()
            return {'msg': 'DatabaseError: transaction is aborted'}, 400

        added_source = postgres.fetchone()
        return added_source, 200


@ns.route('/count')
class SourcesCount(Resource):
    def get(self):
        postgres = postgres_con.cursor()
        postgres.execute(COUNT_SOURCES)
        db_return = postgres.fetchone()

        if db_return:
            return {'count': db_return[0]}, 200

        return {"msg": "Error"}, 400
