from flask import request
from flask_restplus import Resource, reqparse

from apis.db import api
from db import postgres

ns = api.namespace('documents', description="documents api")

@ns.route('/count')
class DocumentsCount(Resource):
    def get(self):
        postgres.execute("SELECT COUNT(*) FROM documents;")
        db_return = postgres.fetchone()

        if db_return:
             return {'count': db_return[0]}, 200
        
        return {"msg": "Error"}, 400
