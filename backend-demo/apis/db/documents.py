from flask import request
from flask_restplus import Resource, reqparse

from apis.db import api
from db import mongo

ns = api.namespace('documents', description="documents api")

@ns.route('/count')
class DocumentsCount(Resource):
    def get(self):
        coll = mongo.db.Documents
        return {'count': coll.find().count()}, 200
