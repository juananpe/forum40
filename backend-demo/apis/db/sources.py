from flask import request
from flask_restplus import Resource, reqparse, fields
from apis.db import api

from db import postgres_con
from db.queries import COUNT_SOURCES

ns = api.namespace('sources', description="sources api")

@ns.route('/count')
class SourcesCount(Resource):
    def get(self):
        postgres = postgres_con.cursor()
        postgres.execute(COUNT_SOURCES)
        db_return = postgres.fetchone()

        if db_return:
             return {'count': db_return[0]}, 200
        
        return {"msg": "Error"}, 400
