from flask import request
from flask_restplus import Resource, reqparse

from apis.db import api
from models.db_models import aggregate_model

from db import mongo
from db.mongo_util import aggregate

ns = api.namespace('users', description="users api")

@ns.route('/count')
class UsersCount(Resource):
    def get(self):
        coll = mongo.db.Users
        return {'count': coll.find().count()}, 200

@ns.route('/aggregate')
@api.expect(aggregate_model)
class UsersAggregate(Resource):
    def post(self):
        coll = mongo.db.Users
        body = api.payload
        return aggregate(coll, body), 200
