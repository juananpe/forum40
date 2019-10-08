from flask import Response
from flask_restplus import Resource, reqparse

from apis.db import api
from models.db_models import comments_parser, comments_parser_sl, groupByModel

from db import mongo
from db import postgres
from db import postgres_json
from db import postgres_con

from db.util import getCommentsByQuery, getCommentById, getLabelIdByName

from db.queries.comments_timeseries import getCommentsGroupedByDay, getCommentsGroupedByMonth, getCommentsGroupedByYear

from datetime import timedelta, date, datetime
from dateutil.relativedelta import relativedelta

from bson import json_util, ObjectId
import json
import sys

from jwt_auth.token import token_required

ns = api.namespace('comments', description="comments api")

def createCommentsQueryFromArgs(args):
    query = {}
    query["timestamp"] = { "$gt" : datetime.strptime('2015-05-31-22','%Y-%m-%d-%H'), "$lt" : datetime.strptime('2016-05-31-22','%Y-%m-%d-%H') }
    if 'label' in args and args['label']:
        labelIds = [getLabelIdByName(i) for i in args['label']]
        # query["labels"] = {
        #     "$elemMatch" : {
        #         "labelId": { "$in": labelIds },
        #         	"$or" : [
        #                     { "manualLabels.label" : 1},
        #                     { "$and" :
        #                         [
        #                             {"classified" : 0}, {"confidence" : {"$ne" : []}}
        #                         ]
        #                     }
        #                 ]
        #             }
        #         }
        query["labels"] = {
            "$elemMatch": {
                "labelId": {"$in": labelIds},
                "classified": 1
            }
        }
    else :
        query["labels"] = {"$exists": 1}
    if 'keyword' in args and args['keyword']:
        searchwords = " ".join(x for x in args['keyword'])
        query["$text"] = {
            "$search" : searchwords,
            "$caseSensitive": False
        }
    return query

def convertObjectToJSonResponse(obj):
    return Response(json.dumps(obj, default=json_util.default), mimetype='application/json')

def convertCursorToJSonResponse(cursor):
    return convertObjectToJSonResponse(list(cursor))

import sys

def getLabelIdByName2(name):
        postgres.execute("SELECT id FROM labels WHERE name = '{0}';".format(name))
        db_return = postgres.fetchone()
        if db_return:
            return db_return[0]
        return -1

def createQuery(args, skip=None, limit=None):
    annotations_sub_query = 'SELECT label_id, comment_id, user_id FROM annotations'
    if 'label' in args and args['label']:
        labelIds = ' WHERE ' + 'label_id IN ({0})'.format(", ".join(str(getLabelIdByName2(i)) for i in args['label']) )
        annotations_sub_query += labelIds

    comments_sub_query = 'SELECT id AS comment_id, user_id, parent_comment_id, title, text FROM comments'
    if 'keyword' in args and args['keyword']:
        searchwords = ' WHERE ' + ' OR '.join("text LIKE '%{0}%'".format(x) for x in args['keyword'])
        comments_sub_query += searchwords

    query = ' ( {0} ) AS a, ( {1} ) AS c WHERE a.comment_id = c.comment_id'.format(annotations_sub_query, comments_sub_query)

    if limit:
        query += " LIMIT " + str(limit)

    if skip:
        query += " OFFSET " + str(skip)

    return query

@ns.route('/')
@api.expect(comments_parser_sl)
class CommentsGet(Resource):
    def get(self):
        args = comments_parser_sl.parse_args()
        skip = args["skip"]
        limit = args["limit"]

        query = 'SELECT * FROM' + createQuery(args, skip, limit) 
        
        postgres_json.execute(query)
        return json.dumps(postgres_json.fetchall())

@ns.route('/count')
@api.expect(comments_parser)
class CommentsCount(Resource):
    def get(self):
        args = comments_parser.parse_args()

        query = 'SELECT COUNT(*) FROM' + createQuery(args)

        postgres_json.execute(query)
        comments_count = postgres_json.fetchone()

        return {"count" : comments_count}

def getLabelsByTime(args, commensByTimeintervall, addMissingIntervalls, formatter):
    coll = mongo.db.Comments
    label = args['label']
    keywords = args['keyword']
    id = getLabelIdByName(label)
    cursor = coll.aggregate(commensByTimeintervall(id, keywords))
    timeseries = addMissingIntervalls(list(cursor))
    response_obj = prepareForVisualisation(timeseries, formatter)
    return convertObjectToJSonResponse(response_obj)

def addMissingDays2(data):
    #el0 = data[0]
    min_ = min_date #date(el0["_id"]['year'], el0["_id"]['month'], el0["_id"]['dayOfMonth'])
    missing = []
    for el in data:
        while min_ < date(el['year'], el['month'], el['day']):
            missing.append({"year": min_.year, "month": min_.month, "day": min_.day, "count": 0})
            min_ = min_ + timedelta(1)
        min_ = min_ + + timedelta(1)
    data = data + missing
    return sorted(data, key=lambda x: (x['year'], x['month'], x['day'] )) 

def addMissingMonths2(data):
    if len(data) == 0:
        return data

    #el0 = data[0] 
    min_ = min_date #date(el0["_id"]['year'], el0["_id"]['month'], 1) 
    missing = []
    for el in data:
        while min_ < date(el['year'], el['month'], 1):
            missing.append({"year": min_.year, "month": min_.month, "count": 0})
            min_ = min_ + relativedelta(months=1)
        min_ = min_ + relativedelta(months=1)
    data = data + missing
    return sorted(data, key=lambda x: (x['year'], x['month'] ))

def addMissingYears2(data):
    if len(data) == 0:
        return data

    min_ = min_date.year # data[0]["_id"]['year']
    missing = []
    for el in data:
        while min_ < el['year']:
            missing.append({"year": min_, "count": 0})
            min_ = min_ + 1
        min_ = min_ + 1
    data = data + missing
    return sorted(data, key=lambda x: (x['year']))

def prepareForVisualisation2(data, f):
    if len(data) == 0:
        return data

    time_list = []
    data_list = []
    for e in data:
        time_list.append(f(e))
        data_list.append(e["count"])
    start_time = data[0]
    del start_time['count']
    return {"start_time": start_time, "time": time_list, "data": data_list}

@ns.route('/groupByDay')
@api.expect(groupByModel)
class CommentsGroupByDay(Resource):
    def get(self):
        args = groupByModel.parse_args()

        annotations_sub_query = ''
        if 'label' in args and args['label']:
            labelIds = ' WHERE ' + 'label_id IN ({0})'.format(args['label'])
            annotations_sub_query += labelIds

        comments_sub_query = ''
        if 'keyword' in args and args['keyword']:
            searchwords = ' WHERE ' + ' OR '.join("text LIKE '%{0}%'".format(x) for x in args['keyword'])
            comments_sub_query += searchwords

        postgres_json.execute("""
            SELECT day, month, year, Count(*) FROM 
                (SELECT label_id,comment_id FROM annotations {0}) AS a, 
                (SELECT id AS comment_id, year, month, day FROM comments {1}) AS c 
            WHERE a.comment_id = c.comment_id
            GROUP BY label_id, year, month, day
            """.format(annotations_sub_query, comments_sub_query))
        db_result = postgres_json.fetchall()

        return prepareForVisualisation2(addMissingDays2(db_result), lambda d : "{}.{}.{}".format(d['day'], d['month'], d['year']))

        #args = groupByModel.parse_args()
        #return getLabelsByTime(
        #    args, 
        #    getCommentsGroupedByDay, 
        #    addMissingDays, 
        #    lambda d : "{}.{}.{}".format(d['dayOfMonth'], d['month'], d['year']))

# TODO 
months =	{
  "1": "Jan.",
  "2": "Feb.",
  "3": "Mär.",
  "4": "Apr.",
  "5": "Mai",
  "6": "Juni",
  "7": "Juli",
  "8": "Aug.",
  "9": "Sep.",
  "10": "Okt.",
  "11": "Nov.",
  "12": "Dez.",
}

@ns.route('/groupByMonth')
@api.expect(groupByModel)
class CommentsGroupByMonth(Resource):
    def get(self):
        args = groupByModel.parse_args()

        annotations_sub_query = ''
        if 'label' in args and args['label']:
            labelIds = ' WHERE ' + 'label_id IN ({0})'.format(args['label'])
            annotations_sub_query += labelIds

        comments_sub_query = ''
        if 'keyword' in args and args['keyword']:
            searchwords = ' WHERE ' + ' OR '.join("text LIKE '%{0}%'".format(x) for x in args['keyword'])
            comments_sub_query += searchwords

        postgres_json.execute("""
            SELECT month, year, Count(*) FROM 
                (SELECT label_id,comment_id FROM annotations {0}) AS a, 
                (SELECT id AS comment_id, year, month FROM comments {1}) AS c 
            WHERE a.comment_id = c.comment_id
            GROUP BY label_id, year, month
            """.format(annotations_sub_query, comments_sub_query))
        db_result = postgres_json.fetchall()
        return prepareForVisualisation2(addMissingMonths2(db_result), lambda d : "{}.{}".format(d['month'], d['year']))
        
        #args = groupByModel.parse_args()
        #return getLabelsByTime(
        #    args, 
        #    getCommentsGroupedByMonth, 
        #    addMissingMonths, 
        #    lambda d : "{} {}".format(months[str(d['month'])], d['year']))

@ns.route('/groupByYear')
@api.expect(groupByModel)
class CommentsGroupByYear(Resource):
    def get(self):
        args = groupByModel.parse_args()

        annotations_sub_query = ''
        if 'label' in args and args['label']:
            labelIds = ' WHERE ' + 'label_id IN ({0})'.format(args['label'])
            annotations_sub_query += labelIds

        comments_sub_query = ''
        if 'keyword' in args and args['keyword']:
            searchwords = ' WHERE ' + ' OR '.join("text LIKE '%{0}%'".format(x) for x in args['keyword'])
            comments_sub_query += searchwords

        postgres_json.execute("""
            SELECT year, Count(*) FROM 
                (SELECT label_id,comment_id FROM annotations {0}) AS a, 
                (SELECT id AS comment_id, year FROM comments {1}) AS c 
            WHERE a.comment_id = c.comment_id
            GROUP BY label_id, year
            """.format(annotations_sub_query, comments_sub_query))
        db_result = postgres_json.fetchall()
        return prepareForVisualisation2(addMissingYears2(db_result), lambda d : "{}".format(d['year']))
        #args = groupByModel.parse_args()
        #return getLabelsByTime(
        #    args, 
        #    getCommentsGroupedByYear, 
        #    addMissingYears, 
        #    lambda d : d['year'])
            
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

        postgres_json.execute('SELECT id, text, title, user_id, year, month, day FROM comments p, (SELECT parent_comment_id FROM comments c WHERE id = {}) as c WHERE p.id = c.parent_comment_id;'.format(id))
        db_result = postgres_json.fetchone()
        if not db_result:
            return {'msg' : "Error: No such Comment"}
        return db_result


@ns.route('/parent_recursive/<string:id>/')
class CommentsParentRec(Resource):
    def get(self, id):
        comments = []

        postgres_json.execute('SELECT id, parent_comment_id, user_id, title, text  FROM comments WHERE id = {0};'.format(id))
        db_response = postgres_json.fetchone()
        
        if db_response:
            id_ = db_response['parent_comment_id']
            while True:
                comments.append(db_response)
                if id_:
                    postgres_json.execute('SELECT id, parent_comment_id, user_id, title, text FROM comments WHERE id = {0};'.format(id_))
                    db_response = postgres_json.fetchone()
                    id_ = db_response['parent_comment_id']
                else:
                    break

        response = {
            "comments" : comments,
            "size" : len(comments)
        }
        return response


def _comment_exists(id):
    postgres.execute("SELECT id FROM comments WHERE id = {0} fetch first 1 rows only;".format(id))
    db_result = postgres.fetchone()
    return db_result != None

def _label_exists(id):
    postgres.execute("SELECT id FROM labels WHERE id = {0} fetch first 1 rows only;".format(id))
    db_result = postgres.fetchone()
    return db_result != None

def _user_exists(id):
    postgres.execute("SELECT id FROM users WHERE id = {0} fetch first 1 rows only;".format(id))
    db_result = postgres.fetchone()
    return db_result != None

import sys

@ns.route('/label2/<int:comment_id>/<int:label_id>/<int:user_id>/<int:label>')
class LabelComment(Resource):
    @token_required
    @api.doc(security='apikey')
    def put(self, data, comment_id ,label_id, user_id, label):

        label = bool(label)

        # Check Args
        if not _comment_exists(comment_id):
            return {"msg": "No Comments with id: {0}".format(comment_id)}, 400

        if not _label_exists(label_id):
            return {"msg": "No Label with id: {0}".format(comment_id)}, 400

        if not _user_exists(user_id):
            return {"msg": "No User with id: {0}".format(comment_id)}, 400

        record_to_select = (label_id, comment_id, user_id)
        postgres_json.execute("SELECT label FROM annotations WHERE label_id = %s AND comment_id = %s AND user_id = '%s';", record_to_select)
        db_result = postgres_json.fetchone()

        print(db_result['label'], label, file=sys.stderr)

        if not db_result: # No Annotation found
            record_to_insert = (label_id, comment_id, user_id, label)
            postgres.execute("INSERT INTO annotations (label_id, comment_id, user_id, label) VALUES (%s, %s, %s, %s)", record_to_insert)
        elif db_result['label'] != label: # Update
            record_to_update = (label, label_id, comment_id, user_id)
            postgres.execute("UPDATE annotations SET label = %s WHERE label_id = %s AND comment_id = %s AND user_id = '%s'", record_to_update)
        else: 
            pass

        postgres_con.commit()

        return "ok", 200
