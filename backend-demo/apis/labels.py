from flask import request
from flask_restplus import Resource, reqparse

from apis import api
from apis import aggregate_parser

from db import mongo
from db.mongo_util import aggregate

ns = api.namespace('labels', description="labels api")

@ns.route('/count')
class LabelsCount(Resource):
    def get(self):
        coll = mongo.db.Labels
        return {'count': coll.find().count()}, 200

@ns.route('/aggregate')
@api.expect(aggregate_parser)
class LabelsTest(Resource):
    def post(self):
        coll = mongo.db.Labels
        body = aggregate_parser.parse_args()
        return aggregate(coll, body), 200