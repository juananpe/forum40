from flask import request
from flask_restplus import Resource, reqparse

from apis.db import api
from db.queries import COUNT_DOCUMENTS
from db import postgres_con

ns = api.namespace('documents', description="documents api")

@ns.route('/count')
class DocumentsCount(Resource):
    def get(self):
        postgres = postgres_con.cursor()
        postgres.execute(COUNT_DOCUMENTS)
        db_return = postgres.fetchone()

        if db_return:
             return {'count': db_return[0]}, 200
        
        return {"msg": "Error"}, 400
