from flask import Response
from flask_restplus import Resource, reqparse

from apis.db import api
from models.db_models import comments_parser, comments_parser_sl, groupByModel

from db import postgres
from db import postgres_json
from db import postgres_con
from db.queries import *

from datetime import timedelta, date, datetime
from dateutil.relativedelta import relativedelta

from bson import json_util, ObjectId
import json
import sys

from jwt_auth.token import token_required

ns = api.namespace('comments', description="comments api")
min_date = date(2015, 6, 1)

def convertObjectToJSonResponse(obj):
    return Response(json.dumps(obj, default=json_util.default), mimetype='application/json')

def convertCursorToJSonResponse(cursor):
    return convertObjectToJSonResponse(list(cursor))


def getLabelIdByName(name):
        postgres.execute(SELECT_ID_FROM_LABELS_BY_NAME(name)) 
        db_return = postgres.fetchone()
        if db_return:
            return db_return[0] 
        return -1

def createQuery(args, skip=None, limit=None):
    annotations_sub_query = 'SELECT DISTINCT comment_id FROM annotations'
    if 'label' in args and args['label']:
        labelIds = ' WHERE ' + 'label_id IN ({0})'.format(", ".join(i for i in args['label']) )
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

def addMissingDays(data):
    min_ = min_date
    missing = []
    for el in data:
        while min_ < date(el['year'], el['month'], el['day']):
            missing.append({"year": min_.year, "month": min_.month, "day": min_.day, "count": 0})
            min_ = min_ + timedelta(1)
        min_ = min_ + + timedelta(1)
    data = data + missing
    return sorted(data, key=lambda x: (x['year'], x['month'], x['day'] )) 

def addMissingMonths(data):
    if len(data) == 0:
        return data

    min_ = min_date
    missing = []
    for el in data:
        while min_ < date(el['year'], el['month'], 1):
            missing.append({"year": min_.year, "month": min_.month, "count": 0})
            min_ = min_ + relativedelta(months=1)
        min_ = min_ + relativedelta(months=1)
    data = data + missing
    return sorted(data, key=lambda x: (x['year'], x['month'] ))

def addMissingYears(data):
    if len(data) == 0:
        return data

    min_ = min_date.year
    missing = []
    for el in data:
        while min_ < el['year']:
            missing.append({"year": min_, "count": 0})
            min_ = min_ + 1
        min_ = min_ + 1
    data = data + missing
    return sorted(data, key=lambda x: (x['year']))

def prepareForVisualisation(data, f):
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

        postgres_json.execute(GROUP_COMMENTS_BY_DAY(annotations_sub_query, comments_sub_query))
        db_result = postgres_json.fetchall()

        return prepareForVisualisation(addMissingDays(db_result), lambda d : "{}.{}.{}".format(d['day'], d['month'], d['year']))

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

        postgres_json.execute(GROUP_COMMENTS_BY_MONTH(annotations_sub_query, comments_sub_query))
        db_result = postgres_json.fetchall()
        return prepareForVisualisation(addMissingMonths(db_result), lambda d : "{}.{}".format(d['month'], d['year']))

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

        postgres_json.execute(GROUP_COMMENTS_BY_YEAR(annotations_sub_query, comments_sub_query))
        db_result = postgres_json.fetchall()
        return prepareForVisualisation(addMissingYears(db_result), lambda d : "{}".format(d['year']))
        

@ns.route('/parent/<string:id>/')
class CommentsParent(Resource):
    def get(self, id):

        # TODO externalize str
        postgres_json.execute('SELECT id, text, title, user_id, year, month, day FROM comments p, (SELECT parent_comment_id FROM comments c WHERE id = {}) as c WHERE p.id = c.parent_comment_id;'.format(id))
        db_result = postgres_json.fetchone()
        if not db_result:
            return {'msg' : "Error: No such Comment"}
        return db_result


@ns.route('/parent_recursive/<string:id>/')
class CommentsParentRec(Resource):
    def get(self, id):
        comments = []

        # TODO externalize str
        postgres_json.execute('SELECT id, parent_comment_id, user_id, title, text  FROM comments WHERE id = {0};'.format(id))
        db_response = postgres_json.fetchone()
        
        if db_response:
            id_ = db_response['parent_comment_id']
            while True:
                comments.append(db_response)
                if id_:
                    # TODO externalize str
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
    postgres.execute(SELECT_COMMENT_BY_ID(id))
    db_result = postgres.fetchone()
    return db_result != None

def _label_exists(id):
    postgres.execute(SELECT_LABEL_BY_ID(id))
    db_result = postgres.fetchone()
    return db_result != None

def _user_exists(id):
    postgres.execute(SELECT_USER_BY_ID(id))
    db_result = postgres.fetchone()
    return db_result != None

import sys

@ns.route('/get_labels/<int:comment_id>')
class GetLabel(Resource):
    def get(self, comment_id):
        postgres_json.execute(f"SELECT label_id, user_id, label FROM Annotations WHERE comment_id = {comment_id}")
        db_return = postgres_json.fetchall()
        return db_return

@ns.route('/add_label/<int:comment_id>/<int:label_id>/<int:user_id>/<int:label>')
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

        postgres_json.execute(SELECT_LABEL_FROM_ANNOTATIONS_BY_IDS(label_id, comment_id, user_id))
        db_result = postgres_json.fetchone()

        if not db_result: # No Annotation found
            postgres.execute(INSERT_ANNOTATION(label_id, comment_id, user_id, label))
        elif db_result['label'] != label: # Update
            postgres.execute(UPDATE_ANNOTATION(label_id, comment_id, user_id, label))
        else: 
            pass

        postgres_con.commit()

        return "ok", 200
