from flask import request
from flask_restplus import Resource, reqparse

from apis.db import api
from models.db_models import aggregate_parser

from db import mongo
from db.mongo_util import aggregate

ns = api.namespace('sources', description="sources api")

@ns.route('/count')
class SourcesCount(Resource):
    def get(self):
        coll = mongo.db.Sources
        return {'count': coll.find().count()}, 200

@ns.route('/aggregate')
@api.expect(aggregate_parser)
class SourcesAggregate(Resource):
    def post(self):
        coll = mongo.db.Sources
        body = aggregate_parser.parse_args()
        return aggregate(coll, body), 200