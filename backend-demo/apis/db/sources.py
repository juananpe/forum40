from flask_restplus import Resource, Namespace
from psycopg2 import DatabaseError
from psycopg2.extras import RealDictCursor

from db import postgres_con
from db.db_models import source_parser
from db.queries import COUNT_SOURCES
from jwt_auth.token import token_required, token_optional

ns = Namespace('sources', description="sources api")


@ns.route('/')
class Sources(Resource):

    @token_optional
    @ns.doc(security='apikey')
    def get(self, data):
        role = None
        if self:
            role = self.get('role', None)
        query = "select * from sources s"

        if role != 'admin':
            query += " where not s.protected"

        postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
        try:
            postgres.execute(query)
            postgres_con.commit()

        except DatabaseError:
            postgres_con.rollback()
            return {'msg': 'DatabaseError: transaction is aborted'}, 400

        sources = postgres.fetchall()
        return sources, 200

    @ns.expect(source_parser)
    @token_required
    @ns.doc(security='apikey')
    def post(self, data):
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
        return {'id': added_source[0]}, 200


@ns.route('/<name>')
class SourcesByName(Resource):

    def get(self, name):
        query = f"select id from sources where name = '{name}'"
        postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
        try:
            postgres.execute(query)
            postgres_con.commit()

        except DatabaseError:
            postgres_con.rollback()
            return {'msg': 'DatabaseError: transaction is aborted'}, 400

        sources = postgres.fetchone()
        if sources:
            return sources, 200
        else:
            return {"id": None}, 200


@ns.route('/count')
class SourcesCount(Resource):
    def get(self):
        postgres = postgres_con.cursor()
        postgres.execute(COUNT_SOURCES)
        db_return = postgres.fetchone()

        if db_return:
            return {'count': db_return[0]}, 200

        return {"msg": "Error"}, 400
