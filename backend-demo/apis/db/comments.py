from flask import request, jsonify, Response
from flask_restplus import Resource, reqparse

from apis.db import api
from models.db_models import label_time_model, comments_parser, comments_parser_sl

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
    labelIds = [ObjectId(getLabelIdVyName(i)) for i in label]
    query = {}
    if len(label) > 0:
        query = {"labels.labelId" : { "$in": labelIds }}
    return coll.find(query)

@ns.route('/')
@api.expect(comments_parser_sl)
class CommentsGet(Resource):
    def get(self):
        args = comments_parser_sl.parse_args()
        label = args["label"]
        if not label:
            label = []
        skip = args["skip"]
        limit = args["limit"]

        cursor = getCommentsByLabel(label)
        comments = list(cursor.skip(skip).limit(limit))
        return Response(json.dumps(comments, default=json_util.default), mimetype='application/json')

@ns.route('/count')
@api.expect(comments_parser)
class CommentsCount(Resource):
    def get(self):
        args = comments_parser.parse_args()
        label = args["label"]
        if not label:
            label = []

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
            return {"msg": "{} is not a valid ObjectId".format(id)}, 400
        if "parentCommentId" in base_comment:
            parent_id = base_comment["parentCommentId"]
            parent_comment = coll.find_one({"_id" : parent_id})
            
            return Response(json.dumps(parent_comment, default=json_util.default), mimetype='application/json')
        else:
            return Response(json.dumps({}, default=json_util.default), mimetype='application/json')

@ns.route('/parent_recursive/<string:id>/')
#@api.expect(comments_model)
class CommentsParentRec(Resource):
    def get(self, id):
        coll = mongo.db.Comments
        try:
            base_comment = coll.find_one({"_id" : ObjectId(id)})
        except:
            return {"msg": "{} is not a valid ObjectId".format(id)}, 400

        if not base_comment:
            return Response(json.dumps([], default=json_util.default), mimetype='application/json')
        
        i = 1
        c_list = [base_comment]

        parent = base_comment
        while "parentCommentId" in parent:
            next_parentId = parent["parentCommentId"]
            next_parent = coll.find_one({"_id" : next_parentId})
            c_list.insert(0, next_parent)
            i += 1
            parent = next_parent
        response = {
            "comments" : c_list,
            "size" : i
        }

        return Response(json.dumps(response, default=json_util.default), mimetype='application/json')

