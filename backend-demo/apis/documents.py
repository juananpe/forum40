from flask import request
from flask_restplus import Resource, reqparse

from apis import api
from apis import aggregate_parser

from db import mongo
from db.mongo_util import aggregate

ns = api.namespace('documents', description="documents api")

@ns.route('/count')
class DocumentsCount(Resource):
    def get(self):
        coll = mongo.db.Documents
        return {'count': coll.find().count()}, 200

@ns.route('/aggregate')
@api.expect(aggregate_parser)
class DocumentsTest(Resource):
    def post(self):
        coll = mongo.db.Documents
        body = aggregate_parser.parse_args()
        return aggregate(coll, body), 200
