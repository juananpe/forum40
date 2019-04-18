from flask import request
from flask_restplus import Resource, reqparse

from apis.db import api
from models.db_models import aggregate_model

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
@api.expect(aggregate_model)
class CommentsTest(Resource):
    def post(self):
        coll = mongo.db.Comments
        body = api.payload
        return aggregate(coll, body), 200
