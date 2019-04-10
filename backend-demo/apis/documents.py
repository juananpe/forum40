from flask_restplus import Resource
from db import mongo
from apis import api

ns = api.namespace('documents', description="documents api")

@ns.route('/')
class DocumentsGet(Resource):
    def get(self):
        return {'hello': 'documents'}, 200

@ns.route('/count')
class DocumentsCount(Resource):
    def get(self):
        coll = mongo.db.Documents
        return {'count': coll.find().count()}, 200
