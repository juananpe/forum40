from flask import Response
from flask_restplus import Resource, reqparse

from apis.db import api
from models.db_models import comments_parser, comments_parser_sl, groupByModel, comment_parser

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
@api.expect(comments_parser_sl)
class CommentsGet2(Resource):
    @token_optional
    @api.doc(security='apikey')
    def get(self, data):
        # get args
        args = comments_parser_sl.parse_args()
        skip = args["skip"]
        limit = args["limit"]
        label_ids = args.get('label', None)
        keywords = args.get('keyword', None)
        user_id = None
        if self:
            user_id = self["user"]

        # get all comments
        query_getIds = GET_COMMENTS_BY_FILTER(label_ids, keywords, skip, limit)

        try:        
            postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
            postgres.execute(query_getIds)
        except DatabaseError:
            postgres_con.rollback()
            return {'msg' : 'DatabaseError: transaction is aborted'}, 400

        comments = postgres.fetchall()
        ids = [ str(i['id']) for i in comments]

        # get all annotations + facts for selection (ids)

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
        for i in range(0, len(comments)):
            comments[i]['timestamp'] = comments[i]['timestamp'].isoformat()
            if annotations:
                comments[i]['annotations'] = dic[comments[i]['id']]

        return comments
        


@ns.route('/count')
@api.expect(comments_parser)
class CommentsCount(Resource):
    def get(self):
        args = comments_parser.parse_args()

        annotations_where_sec = ''
        if 'label' in args and args['label']:
            labelIds = 'label = True and label_id IN ({0})'.format(", ".join(i for i in args['label']))
            annotations_where_sec += ' where ' + labelIds

        comments_where_sec = ''
        if 'keyword' in args and args['keyword']:
            searchwords = ' OR '.join("text LIKE '%{0}%'".format(x) for x in args['keyword'])
            comments_where_sec += ' where ' +  searchwords

        query = f"""
        select count(*) from
        (select * from comments {comments_where_sec}) as c
        inner join 
        (select coalesce(l.cid_a, l.cid_f) as comment_id from 
        ((select distinct comment_id as cid_a from annotations {annotations_where_sec}) as a
        full outer join
        (select distinct comment_id as cid_f from facts {annotations_where_sec} ) as f
        on a.cid_a = f.cid_f) as l
        order by comment_id) _ 
        on c.id = _.comment_id
"""

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
            labelIds = ' WHERE label = True AND label_id IN ({0})'.format(
                args['label'])
            annotations_sub_query += labelIds

        comments_sub_query = ''
        if 'keyword' in args and args['keyword']:
            searchwords = ' WHERE ' + \
                ' OR '.join("text LIKE '%{0}%'".format(x)
                            for x in args['keyword'])
            comments_sub_query += searchwords

        postgres = postgres_con.cursor(cursor_factory=RealDictCursor)

        try:
            postgres.execute(GROUP_COMMENTS_BY_DAY(
                annotations_sub_query, comments_sub_query))
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

        annotations_sub_query = ''
        if 'label' in args and args['label']:
            labelIds = ' WHERE label = True AND label_id IN ({0})'.format(
                args['label'])
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
            return {'msg': 'DatabaseError: transaction is aborted'}, 400

        db_result = postgres.fetchall()
        return prepareForVisualisation(addMissingMonths(db_result), lambda d: "{}.{}".format(d['month'], d['year']))


@ns.route('/groupByYear')
@api.expect(groupByModel)
class CommentsGroupByYear(Resource):
    def get(self):
        args = groupByModel.parse_args()

        annotations_sub_query = ''
        if 'label' in args and args['label']:
            labelIds = ' WHERE label = True AND label_id IN ({0})'.format(
                args['label'])
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
            return {'msg': 'DatabaseError: transaction is aborted'}, 400

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
        label = args["label"]

        postgres = postgres_con.cursor(cursor_factory=RealDictCursor)

        query = "select * from comments where id = %s"

        try:
            postgres.execute(query, (comment_id,))
        except DatabaseError:
            postgres_con.rollback()
            return {'msg': 'DatabaseError: transaction is aborted'}, 400

        comment = postgres.fetchone()
        if comment:
            comment['timestamp'] = comment['timestamp'].isoformat()

            if self and 'user' in self and label:
                user_id = self["user"]
                if user_id:
                    annotation_query = """
                    select coalesce(a.comment_id, f.comment_id) as comment_id, coalesce(a.label_id, f.label_id) as label_id, a.count_true as group_count_true, a.count_false as group_count_false, f.label as ai, f.confidence as ai_pred , a2.label as user from 
                    (select comment_id, label_id, count(label or null) as count_true, count(not label or null) as count_false
                    from annotations 
                    where label_id in %s and comment_id = %s
                    group by comment_id, label_id
                    ) a
                    full outer join 
                    (select * from facts where label_id in %s and comment_id = %s) f
                    ON a.comment_id = f.comment_id and a.label_id = f.label_id
                    left join annotations a2
                    on a.comment_id = a2.comment_id and a.label_id = a2.label_id and user_id = %s
                    order by a.comment_id, a.label_id
                    """

                    try:
                        postgres.execute(annotation_query, (tuple(
                            label), comment_id, tuple(label), comment_id,  user_id))
                    except DatabaseError:
                        postgres_con.rollback()
                        return {'msg': 'DatabaseError: transaction is aborted. Error when fetching annotations'}, 400

                    annotations = postgres.fetchall()
                    if annotations:
                        comment['annotations'] = annotations

            return comment

        return {}
