from flask import Response
from flask_restplus import Resource, reqparse

from apis.db import api
from models.db_models import comments_parser, comments_parser_sl, groupByModel

from db import mongo

from db.queries.comments_timeseries import getCommentsGroupedByDay, getCommentsGroupedByMonth, getCommentsGroupedByYear

from datetime import timedelta, date, datetime
from dateutil.relativedelta import relativedelta

from bson import json_util, ObjectId
import json

ns = api.namespace('comments', description="comments api")

def getLabelIdByName(name):
    coll = mongo.db.Labels
    label = coll.find_one({"description" : name}, {"_id": 1})
    return label["_id"] if label else None

def createCommentsQueryFromArgs(args):
    query = {}
    query["timestamp"] = { "$gt" : datetime.strptime('2015-05-31-22','%Y-%m-%d-%H'), "$lt" : datetime.strptime('2016-05-31-22','%Y-%m-%d-%H') }
    if 'label' in args and args['label']:
        labelIds = [getLabelIdByName(i) for i in args['label']]
        query["labels"] = {
            "$elemMatch" : {
                "labelId": { "$in": labelIds },
                	"$or" : [ 
                            { "manualLabels.label" : 1}, 
                            { "$and" : 
                                [
                                    {"classified" : 0}, {"confidence" : {"$ne" : []}}
                                ]
                            }
                        ]
                    } 
                }
    if 'keyword' in args and args['keyword']:
        searchwords = " ".join(x for x in args['keyword'])
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


@ns.route('/groupByDay')
@api.expect(groupByModel)
class CommentsGroupByDay(Resource):
    def get(self):
        coll = mongo.db.Comments
        args = groupByModel.parse_args()
        label = args['label']
        keywords = args['keyword']
        id = getLabelIdByName(label)
        cursor = coll.aggregate(getCommentsGroupedByDay(id, keywords))
        timeseries = addMissingDays(list(cursor))
        response_obj = prepareForVisualisation(timeseries, lambda d : "{}.{}.{}".format(d['dayOfMonth'], d['month'], d['year']))
        return convertObjectToJSonResponse(response_obj)

@ns.route('/groupByMonth')
@api.expect(groupByModel)
class CommentsGroupByMonth(Resource):
    def get(self):
        coll = mongo.db.Comments
        args = groupByModel.parse_args()
        label = args['label']
        keywords = args['keyword']
        id = getLabelIdByName(label)
        cursor = coll.aggregate(getCommentsGroupedByMonth(id, keywords))
        timeseries = addMissingMonths(list(cursor))
        response_obj = prepareForVisualisation(timeseries, lambda d : "{}.{}".format(d['month'], d['year']))
        return convertObjectToJSonResponse(response_obj)

@ns.route('/groupByYear')
@api.expect(groupByModel)
class CommentsGroupByYear(Resource):
    def get(self):
        coll = mongo.db.Comments
        args = groupByModel.parse_args()
        label = args['label']
        keywords = args['keyword']
        id = getLabelIdByName(label)
        cursor = coll.aggregate(getCommentsGroupedByYear(id, keywords))
        timeseries = addMissingYears(list(cursor))
        response_obj = prepareForVisualisation(timeseries, lambda d : d['year'])
        return convertObjectToJSonResponse(response_obj)

min_date = date(2015, 6, 1)

def addMissingDays(data):
    #el0 = data[0]
    min_ = min_date #date(el0["_id"]['year'], el0["_id"]['month'], el0["_id"]['dayOfMonth'])
    missing = []
    for el in data:
        while min_ < date(el["_id"]['year'], el["_id"]['month'], el["_id"]['dayOfMonth']):
            missing.append({"_id": {"year": min_.year, "month": min_.month, "dayOfMonth": min_.day}, "count": 0})
            min_ = min_ + timedelta(1)
        min_ = min_ + + timedelta(1)
    data = data + missing
    return sorted(data, key=lambda x: (x["_id"]['year'], x["_id"]['month'], x["_id"]['dayOfMonth'] ))

def addMissingMonths(data):
    if len(data) == 0:
        return data

    #el0 = data[0]
    min_ = min_date #date(el0["_id"]['year'], el0["_id"]['month'], 1)
    missing = []
    for el in data:
        while min_ < date(el["_id"]['year'], el["_id"]['month'], 1):
            missing.append({"_id": {"year": min_.year, "month": min_.month}, "count": 0})
            min_ = min_ + relativedelta(months=1)
        min_ = min_ + relativedelta(months=1)
    data = data + missing
    return sorted(data, key=lambda x: (x["_id"]['year'], x["_id"]['month'] ))

def addMissingYears(data):
    if len(data) == 0:
        return data

    min_ = min_date.year # data[0]["_id"]['year']
    missing = []
    for el in data:
        while min_ < el["_id"]['year']:
            missing.append({"_id": {"year": min_}, "count": 0})
            min_ = min_ + 1
        min_ = min_ + 1
    data = data + missing
    return sorted(data, key=lambda x: (x["_id"]['year']))

def prepareForVisualisation(data, f):
    if len(data) == 0:
        return data

    time_list = []
    data_list = []
    for e in data:
        time_list.append(f(e["_id"]))
        data_list.append(e["count"])
    start_time = data[0]["_id"]
    return {"start_time": start_time, "time": time_list, "data": data_list}

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

@ns.route('/label/<string:comment_id>/<string:label_name>/<int:label>')
class LabelComment(Resource):
    def put(self, comment_id,label_name, label):
        
        # check comments_id
        coll_c = mongo.db.Comments
        try:
            comment = coll_c.find_one({"_id" : ObjectId(comment_id)})
        except:
            return {"msg": "{} is not a valid ObjectId".format(comment_id)}, 400

        if not comment:
            return {"msg": "No comment with ObjectId: {}".format(comment_id)}, 400
        
        # check label_name
        coll_l = mongo.db.Labels
        c = coll_l.find_one({"description" : label_name})
        if not c: 
            return {"msg": "Label '{}' do not exist".format(label_name)}, 400

        # check label
        if not (label == 1 or label == 0): 
            return {"msg": "Label is not 1 or 0"}, 400

        if not 'labels' in comment:
            comment['labels'] = []
        
        current_manuel_label = next(
            (x for x in comment['labels'] if x['labelId'] == c["_id"]),
            None
        )

        new_manuel_label = {
            "annotatorId": "hugo",
            "label": label,
            "timestamp": datetime.now()
        }

        if current_manuel_label:
            coll_c.update(
                {"_id": comment["_id"], "labels.labelId" : c["_id"]}, 
                {"$push": {
                    "labels.$.manualLabels": new_manuel_label
                }
            })
        else:
            default_labels = {
                "labelId": c['_id'],
                "classified": 0,
                "confidence": [],
                "manualLabels": [new_manuel_label]
            }

            coll_c.update(
                {"_id": comment["_id"]}, 
                {"$push": {
                    "labels": default_labels
                }
            })

        return "ok", 200