from flask import request
from flask_restplus import Resource, reqparse

from apis import api
from apis import aggregate_parser

from db import mongo
from db.mongo_util import aggregate

ns = api.namespace('users', description="users api")

@ns.route('/count')
class UsersCount(Resource):
    def get(self):
        coll = mongo.db.Users
        return {'count': coll.find().count()}, 200

@ns.route('/aggregate')
@api.expect(aggregate_parser)
class UsersAggregate(Resource):
    def post(self):
        coll = mongo.db.Users
        body = aggregate_parser.parse_args()
        return aggregate(coll, body), 200
