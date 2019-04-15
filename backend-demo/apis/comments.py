from flask import request
from flask_restplus import Resource, reqparse

from apis import api
from apis import aggregate_parser

from db import mongo
from db.mongo_util import aggregate


ns = api.namespace('comments', description="comments api")


@ns.route('/')
class CommentsGet(Resource):
    def get(self):
        return {'hello': 'comments'}, 200

@ns.route('/count')
class CommentsCount(Resource):
    def get(self):
        coll = mongo.db.Comments
        return {'count': coll.find().count()}, 200

@ns.route('/aggregate')
@api.expect(aggregate_parser)
class CommentsTest(Resource):
    def post(self):
        coll = mongo.db.Comments
        body = aggregate_parser.parse_args()
        return aggregate(coll, body), 200

'''
db.getCollection('Comments').aggregate( [
   { $group: { _id: null, myCount: { $sum: 1 } } },
   { $project: { _id: 0 } }
] )

 '''