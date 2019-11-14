from flask import Response
from flask_restplus import Resource, reqparse

from apis.db import api
from models.db_models import comments_parser, comments_parser_sl, groupByModel, comment_parser, comment_parser_post

#from db import postgres
#from db import postgres_json
from db import postgres_con
from db.queries import *

from psycopg2 import DatabaseError

from psycopg2.extras import RealDictCursor

from datetime import timedelta, date, datetime
from dateutil.relativedelta import relativedelta

from jwt_auth.token import token_optional

from bson import json_util, ObjectId
import json
import sys

from jwt_auth.token import token_required

ns = api.namespace('comments', description="comments api")
min_date = date(2003, 4, 23)


def convertObjectToJSonResponse(obj):
    return Response(json.dumps(obj, default=json_util.default), mimetype='application/json')


def convertCursorToJSonResponse(cursor):
    return convertObjectToJSonResponse(list(cursor))


def getLabelIdByName(name):
    postgres = postgres_con.cursor()
    try:
        postgres.execute(SELECT_ID_FROM_LABELS_BY_NAME(name))
    except DatabaseError:
        postgres_con.rollback()
        return {'msg': 'DatabaseError: transaction is aborted'}, 400

    db_return = postgres.fetchone()
    if db_return:
        return db_return[0]
    return -1

import sys

@ns.route('/')
class CommentsGet2(Resource):
    @token_optional
    @api.doc(security='apikey')
    @api.expect(comments_parser_sl)
    def get(self, data):
        # get args
        args = comments_parser_sl.parse_args()
        skip = args["skip"]
        limit = args["limit"]
        label_ids = args.get('label', None)
        keywords = args.get('keyword', None)
        source_ids = args.get('source_id', None)
        user_id = None
        if self:
            user_id = self["user"]

        # count comments
        query = COUNT_COMMENTS_BY_FILTER(label_ids, keywords, source_ids)

        try:        
            postgres = postgres_con.cursor()
            postgres.execute(query)
        except DatabaseError:
            postgres_con.rollback()
            return {'msg' : 'DatabaseError: transaction is aborted'}, 400

        count = postgres.fetchone()[0]

        comments_with_label = []
        comments_without_label = []
        annotations = []
        dic = []

        if skip < count:
            n = (skip + limit) - count
            if n < 0:
                #print('labeled', file=sys.stderr)
                #print(skip, file=sys.stderr)
                #print(limit, file=sys.stderr)
                comments_with_label = getAllComments(label_ids, keywords, source_ids, skip, limit)
                ids = [ str(i['id']) for i in comments_with_label]
                annotations, dic = getAllAnnotations(ids, label_ids, user_id)
            else :
                #print('split', file=sys.stderr)
                #print(skip, limit - n, file=sys.stderr)
                #print(0, n, file=sys.stderr)

                comments_with_label = getAllComments(label_ids, keywords, source_ids, skip, limit - n)
                ids = [ str(i['id']) for i in comments_with_label]
                annotations, dic = getAllAnnotations(ids, label_ids, user_id)
                comments_without_label = getAllUnlabeledComments(label_ids, keywords, source_ids, 0, n)
        else:
            #print('not labeled', file=sys.stderr)
            #print(skip - count , file=sys.stderr)
            #print(limit, file=sys.stderr)

            comments_without_label = getAllUnlabeledComments(label_ids, keywords, source_ids, skip - count, limit)


        # join comments and annotations + facts

        if comments_with_label:
            for i in range(len(comments_with_label)):
                comments_with_label[i]['timestamp'] = comments_with_label[i]['timestamp'].isoformat()
                if annotations:
                    comments_with_label[i]['annotations'] = dic[comments_with_label[i]['id']]


        for i in range(len(comments_without_label)):
            comments_without_label[i]['timestamp'] = comments_without_label[i]['timestamp'].isoformat()

        return comments_with_label + comments_without_label
    
def getAllComments(label_ids, keywords, source_ids, skip, limit):
    query_getIds = GET_COMMENTS_BY_FILTER(label_ids, keywords, source_ids, skip, limit)

    try:        
        postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
        postgres.execute(query_getIds)
    except DatabaseError:
        postgres_con.rollback()
        return {'msg' : 'DatabaseError: transaction is aborted'}, 400

    return postgres.fetchall()

def getAllUnlabeledComments(label_ids, keywords, source_ids, skip, limit):
    query = GET_UNLABELED_COMMENTS_BY_FILTER(label_ids, keywords, source_ids, skip, limit)

    try:        
        postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
        postgres.execute(query)
    except DatabaseError:
        postgres_con.rollback()
        return {'msg' : 'DatabaseError: transaction is aborted'}, 400

    return postgres.fetchall()

def getAllAnnotations(ids, label_ids, user_id):
    annotations = []
    dic = {}
    if label_ids:
        query_comments = GET_ANNOTATIONS_BY_FILTER(ids, label_ids, user_id)

        try:        
            postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
            postgres.execute(query_comments)
        except DatabaseError:
            postgres_con.rollback()
            return {'msg' : 'DatabaseError: transaction is aborted'}, 400

        annotations = postgres.fetchall()

        # convert annotations + facts to dic
        for i in annotations:
            index = i['comment_id']
            if index in dic:
                dic[index].append(i)
            else:
                dic[index] = list()
                dic[index].append(i)
    return annotations, dic

    @api.doc(security='apikey')
    @api.expect(comment_parser_post)
    @token_optional # change to token_required
    def post(self, data):
        args = comment_parser_post.parse_args()
        doc_id = args['doc_id'] if args.get('doc_id', False) else None
        source_id = args['source_id'] if args.get('source_id', False) else None
        user_id = args['user_id'] if args.get('user_id', False) else None
        parent_comment_id = args['parent_comment_id']  if args.get('parent_comment_id', False) else None
        status = args['status'] if args.get('status', False) else None
        title = args['title'] if args.get('title', False) else None
        text = args['text'] if args.get('text', False) else None
        embedding = args['embedding'] if args.get('embedding', False) else None
        timestamp = args['timestamp'] if args.get('timestamp', False) else None


        postgres = postgres_con.cursor()
        insert_query = "INSERT INTO comments (id, doc_id, source_id, user_id, parent_comment_id, status, title, text, embedding, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;"

        try:
            postgres.execute(SELECT_MAX_ID('comments'))
            max_id = postgres.fetchone()[0]
            postgres.execute(insert_query, (max_id+1, doc_id, source_id, user_id, parent_comment_id, status, title, text, embedding, timestamp))
            postgres_con.commit()

        except DatabaseError:
            postgres_con.rollback()
            return {'msg': 'DatabaseError: transaction is aborted'}, 400

        added_comment = postgres.fetchone()
        return added_comment, 200
        
        
# GET_UNLABELD_COMMENTS_BY_FILTER

import sys

@ns.route('/unlabeled')
@api.expect(comments_parser_sl)
class CommentsGetUnlabeld(Resource):

    def get(self):
        # get args
        args = comments_parser_sl.parse_args()
        skip = args["skip"]
        limit = args["limit"]
        label_ids = args.get('label', None)
        keywords = args.get('keyword', None)
        source_ids = args.get('source_id', None)

        # get all comments
        query = GET_UNLABELED_COMMENTS_BY_FILTER(label_ids, keywords, source_ids, skip, limit)

        print(query, file=sys.stderr)

        try:        
            postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
            postgres.execute(query)
        except DatabaseError:
            postgres_con.rollback()
            return {'msg' : 'DatabaseError: transaction is aborted'}, 400

        comments = postgres.fetchall()
        
        for i in range(0, len(comments)):
            comments[i]['timestamp'] = comments[i]['timestamp'].isoformat()

        return comments

@ns.route('/count')
@api.expect(comments_parser)
class CommentsCount(Resource):
    def get(self):
        args = comments_parser.parse_args()

        labels = args['label'] if 'label' in args else None
        keywords = args['keyword'] if 'keyword' in args else None
        source_ids = args['source_id'] if 'source_id' in args else None

        query = COUNT_COMMENTS_BY_FILTER(labels, keywords, source_ids)

        try:        
            postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
            postgres.execute(query)
        except DatabaseError:
            postgres_con.rollback()
            return {'msg' : 'DatabaseError: transaction is aborted'}, 400

        count = postgres.fetchone()

        return {'count': count}


def addMissingDays(data):
    min_ = min_date
    missing = []
    for el in data:
        while min_ < date(el['year'], el['month'], el['day']):
            missing.append(
                {"year": min_.year, "month": min_.month, "day": min_.day, "count": 0})
            min_ = min_ + timedelta(1)
        min_ = min_ + + timedelta(1)
    data = data + missing
    return sorted(data, key=lambda x: (x['year'], x['month'], x['day']))


def addMissingMonths(data):
    if len(data) == 0:
        return data

    min_ = min_date
    missing = []
    for el in data:
        while min_ < date(el['year'], el['month'], 1):
            missing.append(
                {"year": min_.year, "month": min_.month, "count": 0})
            min_ = min_ + relativedelta(months=1)
        min_ = min_ + relativedelta(months=1)
    data = data + missing
    return sorted(data, key=lambda x: (x['year'], x['month']))


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

        labels = args['label'] if 'label' in args else None
        keywords = args['keyword'] if 'keyword' in args else None

        query = GROUP_COMMENTS_BY_DAY(labels, keywords)

        try:
            postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
            postgres.execute(query)
        except DatabaseError:
            postgres_con.rollback()
            return {'msg': 'DatabaseError: transaction is aborted'}, 400

        db_result = postgres.fetchall()

        return prepareForVisualisation(addMissingDays(db_result), lambda d: "{}.{}.{}".format(d['day'], d['month'], d['year']))


@ns.route('/groupByMonth')
@api.expect(groupByModel)
class CommentsGroupByMonth(Resource):
    def get(self):
        args = groupByModel.parse_args()

        labels = args['label'] if 'label' in args else None
        keywords = args['keyword'] if 'keyword' in args else None

        query = GROUP_COMMENTS_BY_MONTH(labels, keywords)

        try:
            postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
            postgres.execute(query)
        except DatabaseError:
            postgres_con.rollback()
            return {'msg': 'DatabaseError: transaction is aborted'}, 400

        db_result = postgres.fetchall()
        return prepareForVisualisation(addMissingMonths(db_result), lambda d: "{}.{}".format(d['month'], d['year']))


@ns.route('/groupByYear')
@api.expect(groupByModel)
class CommentsGroupByYear(Resource):
    def get(self):
        args = groupByModel.parse_args()

        labels = args['label'] if 'label' in args else None
        keywords = args['keyword'] if 'keyword' in args else None

        query = GROUP_COMMENTS_BY_YEAR(labels, keywords)

        try:
            postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
            postgres.execute(query)
        except DatabaseError:
            postgres_con.rollback()
            return {'msg': 'DatabaseError: transaction is aborted'}, 400

        db_result = postgres.fetchall()
        return prepareForVisualisation(addMissingYears(db_result), lambda d: "{}".format(d['year']))


@ns.route('/parent/<string:id>/')
class CommentsParent(Resource):
    def get(self, id):

        query = GET_PARENT_BY_CHILD(id)
    
        try:
            postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
            postgres.execute(query)
        except DatabaseError:
            postgres_con.rollback()
            return {'msg': 'DatabaseError: transaction is aborted'}

        db_result = postgres.fetchone()
        if not db_result:
            return {'msg': "Error: No such Comment"}
        return db_result


@ns.route('/parent_recursive/<string:id>/')
class CommentsParentRec(Resource):
    def get(self, id):
        comments = []

        postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
        # TODO externalize str
        try:
            postgres.execute(
                'SELECT id, parent_comment_id, user_id, title, text, timestamp FROM comments WHERE id = {0};'.format(id))
        except DatabaseError:
            postgres_con.rollback()
            return {'msg': 'DatabaseError: transaction is aborted'}, 400

        db_response = postgres.fetchone()
        db_response['timestamp'] = db_response['timestamp'].isoformat()

        if db_response:
            id_ = db_response['parent_comment_id']
            while True:
                comments.insert(0, db_response)
                if id_:
                    # TODO externalize str
                    postgres.execute(
                        'SELECT id, parent_comment_id, user_id, title, text, timestamp FROM comments WHERE id = {0};'.format(id_))
                    db_response = postgres.fetchone()
                    db_response['timestamp'] = db_response['timestamp'].isoformat()
                    id_ = db_response['parent_comment_id']
                else:
                    break

        response = {
            "comments": comments,
            "size": len(comments)
        }
        return response


@ns.route('/<int:comment_id>/')
@api.expect(comment_parser)
class Comment(Resource):
    @token_optional
    @api.doc(security='apikey')
    def get(self, request, comment_id):
        args = comment_parser.parse_args()

        label_ids = args['label'] if 'label' in args else None
        comment_id = str(comment_id)

        user_id = None
        if self:
            user_id = self["user"]

        query = "select * from comments where id = %s"

        try:
            postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
            postgres.execute(query, (comment_id,))
        except DatabaseError:
            postgres_con.rollback()
            return {'msg': 'DatabaseError: transaction is aborted'}, 400

        comment = postgres.fetchone()
        ids = [comment_id]

        annotations = []
        if label_ids:
            query_comments = GET_ANNOTATIONS_BY_FILTER(ids, label_ids, user_id)

            try:        
                postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
                postgres.execute(query_comments)
            except DatabaseError:
                postgres_con.rollback()
                return {'msg' : 'DatabaseError: transaction is aborted'}, 400

            annotations = postgres.fetchall()

            # convert annotations + facts to dic
            dic = {}
            for i in annotations:
                index = i['comment_id']
                if index in dic:
                    dic[index].append(i)
                else:
                    dic[index] = list()
                    dic[index].append(i)

        # join comments and annotations + facts
        comment['timestamp'] = comment['timestamp'].isoformat()
        if annotations:
            comment['annotations'] = dic[comment['id']]

        return comment
