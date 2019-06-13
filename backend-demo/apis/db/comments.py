from flask import Response
from flask_restplus import Resource, reqparse

from apis.db import api
from models.db_models import label_time_model, comments_parser, comments_parser_sl, timeseries_parser, timeseries_parser_single

from db import mongo
from db.mongo_util import aggregate

from db.queries.comments_timeseries import get as comments_as_timeseries_aggregate_query
from db.queries.comments_timeseries_multi import get as comments_as_timeseries_aggregate_query_multi
from db.queries.comments_timeseries_single import get as comments_as_timeseries_aggregate_query_single

from bson import json_util, ObjectId

import json

ns = api.namespace('comments', description="comments api")

def getLabelIdByName(name):
    coll = mongo.db.Labels
    label = coll.find_one({"description" : name}, {"_id": 1})
    return label["_id"] if label else None

def createCommentsQueryFromArgs(args):
    query = {}
    if 'label' in args and args['label']:
        labelIds = [getLabelIdByName(i) for i in args['label']]
        query["labels"] = {
            "$elemMatch" : {
                "labelId": { "$in": labelIds },
                "manualLabels.label" : 1
            } 
        }
    if 'keyword' in args and args['keyword']:
        searchwords = " ".join("\"{}\"".format(x) for x in args['keyword'])
        query["$text"] = {
            "$search" : searchwords,
            "$caseSensitive": False
        }
    return query

def getCursorByQuery(query):
    coll = mongo.db.Comments
    return coll.find(query)

def convertObjectToJSonResponse(obj):
    return Response(json.dumps(obj, default=json_util.default), mimetype='application/json')

def convertCursorToJSonResponse(cursor):
    return convertObjectToJSonResponse(list(cursor))

@ns.route('/')
@api.expect(comments_parser_sl)
class CommentsGet(Resource):
    def get(self):
        args = comments_parser_sl.parse_args()
        skip = args["skip"]
        limit = args["limit"]

        query = createCommentsQueryFromArgs(args)
        cursor = getCursorByQuery(query).skip(skip).limit(limit)
        response = convertCursorToJSonResponse(cursor)
        return response

@ns.route('/count')
@api.expect(comments_parser)
class CommentsCount(Resource):
    def get(self):
        args = comments_parser.parse_args()

        query = createCommentsQueryFromArgs(args)
        comments_count = getCursorByQuery(query).count()
        return {"count" : comments_count}

@ns.route('/timeseries')
@api.expect(label_time_model)
class CommentsTimeseries(Resource):

    @api.deprecated
    def post(self):
        coll = mongo.db.Comments
        body = api.payload
        label = body['name']
        time_intervall = body['time_intervall']
        id = getLabelIdByName(label)
        cursor = coll.aggregate(comments_as_timeseries_aggregate_query(id, time_intervall))
        return convertCursorToJSonResponse(cursor)

@ns.route('/timeseries_multi')
@api.expect(timeseries_parser)
class CommentsTimeseriesMulti(Resource):
    def get(self):
        coll = mongo.db.Comments
        args = timeseries_parser.parse_args()
        labels = args['label']
        time_intervall = args['time_intervall']
        ids = [getLabelIdByName(label) for label in labels] if labels else []
        cursor = coll.aggregate(comments_as_timeseries_aggregate_query_multi(ids, time_intervall))
        return convertCursorToJSonResponse(cursor)

@ns.route('/timeseries_single')
@api.expect(timeseries_parser_single)
class CommentsTimeseriesSingle(Resource):
    def get(self):
        coll = mongo.db.Comments
        args = timeseries_parser_single.parse_args()
        label = args['label']
        time_intervall = args['time_intervall']
        id = getLabelIdByName(label)
        cursor = coll.aggregate(comments_as_timeseries_aggregate_query_single(id, time_intervall))
        timeseries = addMissingTimeSlots(list(cursor), time_intervall)
        response_obj = prepareForVisualisation(timeseries)
        return convertObjectToJSonResponse(response_obj)

def addMissingTimeSlots(data, time_intervall):
    min_ = data[0].get("time")
    missing = []
    for el in data:
        while min_ < el.get("time"):
            missing.append({"time": min_, "count": 0})
            min_ = min_ + time_intervall
        min_ = min_ + time_intervall
    data = data + missing
    return sorted(data, key=lambda x: x["time"])

def prepareForVisualisation(data):
    time_list = []
    data_list = []
    for e in data:
        time_list.append(e["time"])
        data_list.append(e["count"])
    return {"time": time_list, "data": data_list} 

@ns.route('/parent/<string:id>/')
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
            return convertObjectToJSonResponse(parent_comment)
        else:
            return convertObjectToJSonResponse({})

@ns.route('/parent_recursive/<string:id>/')
class CommentsParentRec(Resource):
    def get(self, id):
        coll = mongo.db.Comments
        try:
            base_comment = coll.find_one({"_id" : ObjectId(id)})
        except:
            return {"msg": "{} is not a valid ObjectId".format(id)}, 400

        if not base_comment:
            return convertObjectToJSonResponse([])
        
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
        return convertObjectToJSonResponse(response)

