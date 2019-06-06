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


def getLabelIdVyName(name):
    coll = mongo.db.Labels
        
    c = coll.find_one({"description" : name}, {"_id": 1})
    id = None
    if c: 
        id = str(c["_id"])
    return id

def getCommentsByLabel(label):
    coll = mongo.db.Comments
    id = getLabelIdVyName(label)
    return coll.find({"labels.labelId" : ObjectId(id)})

@ns.route('/<string:label>/<int:skip>/<int:limit>')
#@api.expect(comments_model)
class CommentsGet(Resource):
    def get(self, label, skip, limit):
        cursor = getCommentsByLabel(label)
        comments = list(cursor.skip(skip).limit(limit))
        return Response(json.dumps(comments, default=json_util.default), mimetype='application/json')

@ns.route('/<string:label>/count')
#@api.expect(comments_model)
class CommentsCount(Resource):
    def get(self, label):
        cursor = getCommentsByLabel(label)
        comments_count = cursor.count()
        return {"count" : comments_count}

@ns.route('/timeseriesByLabel')
@api.expect(label_time_model)
class CommentssTest(Resource):
    def post(self):
        coll = mongo.db.Comments
        body = api.payload
        label = body['name']
        time_intervall = body['time_intervall']
        id = getLabelIdVyName(label)
        cursor = list(coll.aggregate(clbt(id, time_intervall)))
        return Response(json.dumps(cursor, default=json_util.default), mimetype='application/json')

@ns.route('/parent/<string:id>/')
#@api.expect(comments_model)
class CommentsParent(Resource):
    def get(self, id):
        coll = mongo.db.Comments
        try:
            base_comment = coll.find_one({"_id" : ObjectId(id)})
        except:
            return {"msg": "{} is not a valid ObjectId".format(id)}
        if base_comment:
            parent_id = base_comment["parentDocumentId"]
            parent_comment = coll.find_one({"_id" : parent_id})
            return Response(json.dumps(parent_comment, default=json_util.default), mimetype='application/json')
