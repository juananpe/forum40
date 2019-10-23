from flask import Response
from flask_restplus import Resource, reqparse

from apis.db import api
from models.db_models import comments_parser, comments_parser_sl, groupByModel

#from db import postgres
#from db import postgres_json
from db import postgres_con
from db.queries import *

from psycopg2 import DatabaseError

from psycopg2.extras import RealDictCursor

from datetime import timedelta, date, datetime
from dateutil.relativedelta import relativedelta

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
        return {'msg' : 'DatabaseError: transaction is aborted'}, 400
    
    db_return = postgres.fetchone()
    if db_return:
        return db_return[0]
    return -1

def createQuery(args, skip=None, limit=None):

    annotations_where_sec = ''
    if 'label' in args and args['label']:
        labelIds = 'a.label_id IN ({0})'.format(", ".join(i for i in args['label']))
        annotations_where_sec += labelIds

    comments_where_sec = ''
    if 'keyword' in args and args['keyword']:
        searchwords = ' OR '.join("c.text LIKE '%{0}%'".format(x) for x in args['keyword'])
        comments_where_sec += searchwords

    where_sec = ''
    if annotations_where_sec or comments_where_sec:
        where_sec = 'WHERE'

    and_sec = ''
    if annotations_where_sec and comments_where_sec:
        and_sec = 'AND'

    limit_sec = ''
    if limit:
        limit_sec = " LIMIT " + str(limit)

    offset_sec = ''
    if skip:
        offset_sec = " OFFSET " + str(skip)

    query = f"""
    SELECT c.id, c.title, c.text, c.timestamp, array_agg(a.label_id) as labels
    FROM "comments" as c LEFT OUTER JOIN "annotations" AS a
    ON c.id = a.comment_id
    {where_sec} {annotations_where_sec} {and_sec} {comments_where_sec}
    GROUP BY c.id
    {limit_sec}
    {offset_sec}
    """
    return query

import sys

@ns.route('/')
@api.expect(comments_parser_sl)
class CommentsGet(Resource):
    def get(self):
        args = comments_parser_sl.parse_args()
        skip = args["skip"]
        limit = args["limit"]
        user_id = args["user_id"]

        annotations_where_sec = ''
        if 'label' in args and args['label']:
            labelIds = ' label_id IN ({0})'.format(", ".join(i for i in args['label']))
            annotations_where_sec += labelIds

        where = ''
        if annotations_where_sec:
            where = 'WHERE'

        comments_where_sec = ''
        if 'keyword' in args and args['keyword']:
            searchwords = ' OR '.join("text LIKE '%{0}%'".format(x) for x in args['keyword'])
            comments_where_sec += 'WHERE ' +  searchwords


        postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
        query = f"""
        SELECT _.id, _.title, _.text, _.timestamp, array_agg(_.agg) as group_annotation FROM
        (
            SELECT c.id, c.title, c.text, c.timestamp, ARRAY[a.label_id, count(a.label or null), count(not a.label or null)] as agg
                FROM (SELECT * FROM comments {comments_where_sec} LIMIT {limit} OFFSET {skip}) AS c 
                LEFT OUTER JOIN 
                (SELECT * FROM annotations {where} {annotations_where_sec}) AS a
                ON c.id = a.comment_id
                GROUP BY c.id, a.label_id, c.title, c.text, c.timestamp
        ) _ 
        GROUP BY _.id, _.title, _.text, _.timestamp
        """

        user_sec = ''
        if user_id:
            where = 'WHERE'
            user_sec = f"user_id = '{user_id}'"

        and_ = ''
        if annotations_where_sec and user_id:
            and_ = 'AND'

        user_annotations = []

        if 'user_id' in args and args['user_id']:
            query_user = f"""
                SELECT _.id, array_agg(_.agg) as user_annotation FROM
                (
                    SELECT c.id, ARRAY[a.label_id, a.label::int] as agg
                        FROM (SELECT * FROM comments {comments_where_sec} LIMIT {limit} OFFSET {skip}) AS c 
                        LEFT OUTER JOIN 
                        (SELECT * FROM annotations {where} {annotations_where_sec} {and_} {user_sec}) AS a
                        ON c.id = a.comment_id
                        GROUP BY c.id, a.label_id, a.label
                ) _ 
                GROUP BY _.id
            """

            try:
                postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
                postgres.execute(query_user)
            except DatabaseError:
                postgres_con.rollback()
                return {'msg' : 'DatabaseError: transaction is aborted'}, 400

            user_annotations = postgres.fetchall()


        try:        
            postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
            postgres.execute(query)
        except DatabaseError:
            postgres_con.rollback()
            return {'msg' : 'DatabaseError: transaction is aborted'}, 400

        comments = postgres.fetchall()

        for i in range(0, len(comments)):
            print(query_user, file=sys.stderr)
            print(user_annotations, file=sys.stderr)
            comments[i]['timestamp'] = comments[i]['timestamp'].isoformat()
            if user_annotations:
                comments[i]['user_annotation'] = user_annotations[i]['user_annotation']

        return comments
#        args = comments_parser_sl.parse_args()
#        skip = args["skip"]
#        limit = args["limit"]
#
#        query = createQuery(args, skip, limit)
#
#        postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
#
#        try:        
#            postgres.execute(query)
#        except DatabaseError:
#            postgres_con.rollback()
#            return {'msg' : 'DatabaseError: transaction is aborted'}, 400
#
#        comments = postgres.fetchall()
#        for c in comments:
#            c['timestamp'] = c['timestamp'].isoformat()
#
#        return comments


@ns.route('/count')
@api.expect(comments_parser)
class CommentsCount(Resource):
    def get(self):
        args = comments_parser.parse_args()

        query = f'SELECT COUNT(*) FROM ({createQuery(args)}) as foo'

        postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
        postgres.execute(query)
        comments_count = postgres.fetchone()
        return {"count": comments_count}


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

        annotations_sub_query = ''
        if 'label' in args and args['label']:
            labelIds = ' WHERE ' + 'label_id IN ({0})'.format(args['label'])
            annotations_sub_query += labelIds

        comments_sub_query = ''
        if 'keyword' in args and args['keyword']:
            searchwords = ' WHERE ' + \
                ' OR '.join("text LIKE '%{0}%'".format(x)
                            for x in args['keyword'])
            comments_sub_query += searchwords

        postgres = postgres_con.cursor(cursor_factory=RealDictCursor)

        try:        
            postgres.execute(GROUP_COMMENTS_BY_DAY(annotations_sub_query, comments_sub_query))
        except DatabaseError:
            postgres_con.rollback()
            return {'msg' : 'DatabaseError: transaction is aborted'}, 400

        db_result = postgres.fetchall()

        return prepareForVisualisation(addMissingDays(db_result), lambda d: "{}.{}.{}".format(d['day'], d['month'], d['year']))


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
            searchwords = ' WHERE ' + \
                ' OR '.join("text LIKE '%{0}%'".format(x)
                            for x in args['keyword'])
            comments_sub_query += searchwords

        postgres = postgres_con.cursor(cursor_factory=RealDictCursor)

        try:        
            postgres.execute(GROUP_COMMENTS_BY_MONTH(
            annotations_sub_query, comments_sub_query))
        except DatabaseError:
            postgres_con.rollback()
            return {'msg' : 'DatabaseError: transaction is aborted'}, 400
        
        db_result = postgres.fetchall()
        return prepareForVisualisation(addMissingMonths(db_result), lambda d: "{}.{}".format(d['month'], d['year']))


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
            searchwords = ' WHERE ' + \
                ' OR '.join("text LIKE '%{0}%'".format(x)
                            for x in args['keyword'])
            comments_sub_query += searchwords

        postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
        try:        
            postgres.execute(GROUP_COMMENTS_BY_YEAR(
            annotations_sub_query, comments_sub_query))
        except DatabaseError:
            postgres_con.rollback()
            return {'msg' : 'DatabaseError: transaction is aborted'}, 400

        
        db_result = postgres.fetchall()
        return prepareForVisualisation(addMissingYears(db_result), lambda d: "{}".format(d['year']))


@ns.route('/parent/<string:id>/')
class CommentsParent(Resource):
    def get(self, id):

        # TODO externalize str
        postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
        try:        
            postgres.execute(
            'SELECT id, text, title, user_id, year, month, day FROM comments p, (SELECT parent_comment_id FROM comments c WHERE id = {}) as c WHERE p.id = c.parent_comment_id;'.format(id))
        except DatabaseError:
            postgres_con.rollback()
            return {'msg' : 'DatabaseError: transaction is aborted'}
        
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
            return {'msg' : 'DatabaseError: transaction is aborted'}, 400

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
