from flask_restplus import Resource
from db import mongo
from apis import api

ns = api.namespace('labels', description="labels api")

@ns.route('/')
class LabelsGet(Resource):
    def get(self):
        return {'hello': 'documents'}, 200

@ns.route('/count')
class LabelsCount(Resource):
    def get(self):
        coll = mongo.db.Labels
        return {'count': coll.find().count()}, 200
