from flask_restplus import Resource
from db import mongo
from apis import api

ns = api.namespace('sources', description="sources api")

@ns.route('/')
class SourcesGet(Resource):
    def get(self):
        return {'hello': 'sources'}, 200

@ns.route('/count')
class SourcesCount(Resource):
    def get(self):
        coll = mongo.db.Sources
        return {'count': coll.find().count()}, 200
