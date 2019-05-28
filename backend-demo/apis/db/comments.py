from flask import request, jsonify, Response
from flask_restplus import Resource, reqparse

from apis.db import api
from models.db_models import aggregate_model, label_time_model, comments_model

from db import mongo
from db.mongo_util import aggregate

from db.queries.comments_label_by_time import get as clbt
from bson import json_util, ObjectId

import json

ns = api.namespace('comments', description="comments api")


@ns.route('/<string:label>/<int:skip>/<int:limit>')
#@api.expect(comments_model)
class CommentsGet(Resource):
    def get(self, label, skip, limit):

        # get id
        coll = mongo.db.Labels
        
        c = coll.find_one({"description" : label}, {"_id": 1})
        id = None
        if c: 
            id = str(c["_id"])
        
        comments_collection = mongo.db.Comments
        comments = list(comments_collection.find({"labels.labelId" : ObjectId(id)}).skip(skip).limit(limit))
        return Response(json.dumps(comments, default=json_util.default),
                mimetype='application/json')


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


@ns.route('/timeseriesByLabel')
@api.expect(label_time_model)
class CommentssTest(Resource):
    def post(self):
        # get id
        coll = mongo.db.Labels
        body = api.payload
        
        name = body['name']
        c = coll.find_one({"description" : name}, {"_id": 1})
        id = None
        if c: 
            id = str(c["_id"])

        # aggregate comments
        coll = mongo.db.Comments
        body = api.payload
        cursor = list(coll.aggregate(clbt(id, body['time_intervall'])))
        return Response(json.dumps(cursor, default=json_util.default), mimetype='application/json')
