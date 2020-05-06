from flask import Response, request
from flask_restplus import Resource, reqparse

from apis.db import api
from db.db_models import *

#from db import postgres
#from db import postgres_json
from db import postgres_con, db_cursor
from db.queries import *

from psycopg2.extras import execute_values
import functools
import operator
import sys

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
min_date = date(2016, 6, 1)


def convertObjectToJSonResponse(obj):
    return Response(json.dumps(obj, default=json_util.default), mimetype='application/json')


def convertCursorToJSonResponse(cursor):
    return convertObjectToJSonResponse(list(cursor))


def getLabelIdByName(name):
    query = SELECT_ID_FROM_LABELS_BY_NAME(name)

    db_return = []
    with db_cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        db_return = cur.fetchone()

    if db_return:
        return db_return[0]
    return -1

import sys

def getAllUnlabeledComments(label_ids, keywords, source_ids, skip, limit):
    query = GET_UNLABELED_COMMENTS_BY_FILTER(label_ids, keywords, source_ids, skip, limit)

    res = []
    with db_cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        res = cur.fetchall()
    return res

def getAllAnnotations(ids, label_ids, user_id):
    annotations = []
    dic = {}
    if label_ids:
        query_comments = GET_ANNOTATIONS_BY_FILTER(ids, label_ids, user_id)

        annotations = []
        with db_cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query_comments)
            annotations = cur.fetchall()

        # convert annotations + facts to dic
        for i in annotations:
            index = i['comment_id']
            if index in dic:
                dic[index].append(i)
            else:
                dic[index] = list()
                dic[index].append(i)
    return annotations, dic

def getCommentByIds(id, external_id):
    query = f"select id from comments where source_id = '{id}' and external_id = '{external_id}'"
    postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
    try:
        postgres.execute(query)
        postgres_con.commit()

    except DatabaseError:
        postgres_con.rollback()
        return {'msg': 'DatabaseError: transaction is aborted'}, False

    return postgres.fetchone(), True


@ns.route('/')
class CommentsGet(Resource):
    @token_optional
    @api.doc(security='apikey')
    @api.expect(comments_parser_sl)
    def get(self, data):
        # get args
        args = comments_parser_sl.parse_args()
        skip = args["skip"]
        limit = args["limit"]
        label_ids = args.get('label', None)
        keywords = args.get('keyword', [])
        order = args.get('order', None)
        label_sort_id = args.get('label_sort_id', None)
        source_id = args.get('source_id', None)
        user_id = None
        if self:
            user_id = self["user_id"]

        if not keywords:
            keywords = []
        else:
            keywords = [f"%{kw}%" for kw in keywords]

        # No label is selected
        if not label_ids:
            get_all_comments_query = GET_ALL_COMMENTS(len(keywords))
            with db_cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(get_all_comments_query, (source_id, *keywords, limit, skip))
                comments = cur.fetchall()
                for c in comments:
                    c['timestamp'] = c['timestamp'].isoformat()
            return comments
        
        # Labels selected
        comments_query = GET_COMMENT_IDS_BY_FILTER(label_sort_id, order, label_ids, len(keywords))

        with db_cursor(cursor_factory=RealDictCursor) as cur:

            sort_id = label_sort_id if label_sort_id else label_ids[0]

            cur.execute(comments_query, (source_id, sort_id, *keywords, limit, skip))
            comments = cur.fetchall()
            comment_ids = []
            for c in comments:
                comment_ids.append(c['id'])
                c['timestamp'] = c['timestamp'].isoformat()

        if not comment_ids: # 
            return []

        facts_query = GET_FACTS()
        with db_cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(facts_query, (tuple(comment_ids), tuple(label_ids)))
            facts = cur.fetchall()
        
        annotations_query = GET_ANNOTATIONS()
        with db_cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(annotations_query, (tuple(comment_ids), tuple(label_ids)))
            annotations = cur.fetchall()

        if user_id: # Get user annotations if user logged in
            with db_cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(SELECT_USERS_ANNOTATION, (user_id, tuple(label_ids), tuple(comment_ids) ))
                user_annotations = cur.fetchall()

        label_id = label_sort_id

        for c in comments:
            comment_id = c['id']
            c['annotations'] = []
            filtered_facts = list(filter(lambda x: x['comment_id'] == comment_id, facts))
            filtered_annotations = list(filter(lambda x: x['comment_id'] == comment_id, annotations))
            if user_id:
                filtered_user_annotations = list(filter(lambda x: x['comment_id'] == comment_id, user_annotations)) 

            for label_id in label_ids:
                facts_for_label = list(filter(lambda x: x['label_id'] == label_id, filtered_facts))            
                annotation_for_label = list(filter(lambda x: x['label_id'] == label_id, filtered_annotations))
                if user_id:
                    user_annotation_for_label = list(filter(lambda x: x['label_id'] == label_id, filtered_user_annotations))
                else:
                    user_annotation_for_label = None

                label = {
                    "comment_id": comment_id,
                    "label_id": label_id,
                    "group_count_true": annotation_for_label[0]['count_true'] if annotation_for_label else None,
                    "group_count_false": annotation_for_label[0]['count_false'] if annotation_for_label else None,
                    "ai": facts_for_label[0]['confidence']>=0.5 if facts_for_label else None,
                    "ai_pred": facts_for_label[0]['confidence'] if facts_for_label else None,
                    "user": user_annotation_for_label[0]['label'] if user_annotation_for_label else None
                }
                c['annotations'].append(label)
            
        return comments



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
        external_id = args['external_id'] if args.get('external_id', False) else None

        comm, _ = getCommentByIds(source_id, external_id)
        if comm:
             return {'id': comm['id'], 'source_id': source_id, 'external_id': external_id, 'existed':True}, 200

        time = timestamp.split('T')[0].split('-')
        if len(time) < 3:
            time = [-1, -1, -1]

        insert_query = "INSERT INTO comments (id, doc_id, source_id, user_id, parent_comment_id, status, title, text, embedding, timestamp, external_id, year, month, day) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;"

        max_id = []
        with db_cursor() as cur:
            cur.execute(SELECT_MAX_ID('comments'))
            max_id = cur.fetchone()[0]

        # if the table is empty:
        if max_id is None:
            max_id = -1

        added_comment = []
        with db_cursor() as cur:
            cur.execute(insert_query, (max_id+1, doc_id, source_id, user_id, parent_comment_id, status, title, text, embedding, timestamp, external_id, int(time[0]), int(time[1]), int(time[2])))
            added_comment = cur.fetchone()

        return {'id': added_comment[0]}, 200

        
@ns.route('/json')
class CommentsInsertMany(Resource):
    @token_optional
    @api.doc(security='apikey')
    @api.expect(comments_list_parser)
    def post(self, data):
        comments = request.json
        return insert_new_comments(comments)


def check_comment(args, pk):
    doc_id = args['doc_id'] if args.get('doc_id', False) else None
    source_id = args['source_id'] if args.get('source_id', False) else None
    user_id = args['user_id'] if args.get('user_id', False) else None
    parent_comment_id = args['parent_comment_id']  if args.get('parent_comment_id', False) else None
    status = args['status'] if args.get('status', False) else None
    title = args['title'] if args.get('title', False) else None
    text = args['text'] if args.get('text', False) else None
    embedding = args['embedding'] if args.get('embedding', False) else None
    timestamp = args['timestamp'] if args.get('timestamp', False) else None
    external_id = args['external_id'] if args.get('external_id', False) else None

    comm, _ = getCommentByIds(source_id, external_id)
    if comm:
        return None

    time = timestamp.split('T')[0].split('-')
    if len(time) < 3:
        time = [-1, -1, -1]

    return (pk, doc_id, source_id, user_id, parent_comment_id, status, title, text, embedding, timestamp, external_id, int(time[0]), int(time[1]), int(time[2]))

def insert_new_comments(comments):
    if type(comments) != list:
        return {'msg': 'passed data is not a list of json objects'}, 400
    ## TODO sequence id 
    # create pk
    max_id = []
    with db_cursor() as cur:
        cur.execute(SELECT_MAX_ID('comments'))
        max_id = cur.fetchone()[0]
    # if the table is empty:
    if max_id is None:
        max_id = -1

    ress = []
    for comment in comments:
        res = check_comment(comment, max_id+1)
        if res:
            ress.append(res)
            max_id += 1

    insert_query = "INSERT INTO comments (id, doc_id, source_id, user_id, parent_comment_id, status, title, text, embedding, timestamp, external_id, year, month, day) VALUES %s RETURNING id;"

    added_comment = []
    if ress:
        with db_cursor() as cur:
            added_comment = execute_values(cur,
                insert_query, 
                ress)
            added_comment = cur.fetchall()

    # get args
    new_comments_ids = functools.reduce(operator.iconcat, added_comment, [])
    return {'added_comment_ids' : new_comments_ids, 'count' : len(new_comments_ids)}, 200

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

        comments = []
        with db_cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            comments = cur.fetchall()
        
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

        count = None
        with db_cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            count = cur.fetchone()

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
        return {"start_time": None, "time": [], "data": []}

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
        source_id = args['source_id'] if 'source_id' in args else None

        if labels is None:
            # no label id: select all comments, but filtered by source and keywords
            query = GROUP_ALL_COMMENTS_BY_DAY(keywords, source_id)
        else:
            query = GROUP_COMMENTS_BY_DAY(labels, keywords, source_id)

        db_result = None
        with db_cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            db_result = cur.fetchall()

        return prepareForVisualisation(addMissingDays(db_result), lambda d: "{}.{}.{}".format(d['day'], d['month'], d['year']))


@ns.route('/groupByMonth')
@api.expect(groupByModel)
class CommentsGroupByMonth(Resource):
    def get(self):
        args = groupByModel.parse_args()

        labels = args['label'] if 'label' in args else None
        keywords = args['keyword'] if 'keyword' in args else None
        source_id = args['source_id'] if 'source_id' in args else None

        if labels is None:
            # no label id: select all comments, but filtered by source and keywords
            query = GROUP_ALL_COMMENTS_BY_MONTH(keywords, source_id)
        else:
            query = GROUP_COMMENTS_BY_MONTH(labels, keywords, source_id)

        db_result = None
        with db_cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            db_result = cur.fetchall()

        return prepareForVisualisation(addMissingMonths(db_result), lambda d: "{}.{}".format(d['month'], d['year']))


@ns.route('/groupByYear')
@api.expect(groupByModel)
class CommentsGroupByYear(Resource):
    def get(self):
        args = groupByModel.parse_args()

        labels = args['label'] if 'label' in args else None
        keywords = args['keyword'] if 'keyword' in args else None
        source_id = args['source_id'] if 'source_id' in args else None

        if labels is None:
            # no label id: select all comments, but filtered by source and keywords
            query = GROUP_ALL_COMMENTS_BY_YEAR(keywords, source_id)
        else:
            query = GROUP_COMMENTS_BY_YEAR(labels, keywords, source_id)

        db_result = None
        with db_cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            db_result = cur.fetchall()

        return prepareForVisualisation(addMissingYears(db_result), lambda d: "{}".format(d['year']))


@ns.route('/parent/<string:id>/')
class CommentsParent(Resource):
    def get(self, id):

        query = GET_PARENT_BY_CHILD(id)
    
        db_result = None
        with db_cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            db_result = cur.fetchall()

        
        if not db_result:
            return {'msg': "Error: No such Comment"}
        return db_result


@ns.route('/parent_recursive/<string:id>/')
class CommentsParentRec(Resource):
    def get(self, id):
        comments = []

        query = 'SELECT id, parent_comment_id, user_id, title, text, timestamp FROM comments WHERE id = {0};'.format(id)

        db_response = []
        with db_cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            db_response = cur.fetchone()

        db_response['timestamp'] = db_response['timestamp'].isoformat()

        if db_response:
            id_ = db_response['parent_comment_id']
            while True:
                comments.insert(0, db_response)
                if id_:
                    
                    query = 'SELECT id, parent_comment_id, user_id, title, text, timestamp FROM comments WHERE id = {0};'.format(id_)

                    db_response = []
                    with db_cursor(cursor_factory=RealDictCursor) as cur:
                        cur.execute(query)
                        db_response = cur.fetchone()

                    if db_response:
                        db_response['timestamp'] = db_response['timestamp'].isoformat()
                        id_ = db_response['parent_comment_id']
                    else:
                        break
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
            user_id = self["user_id"]

        query = "select * from comments where id = %s"

        comment = None
        with db_cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (comment_id,))
            comment = cur.fetchone()

        ids = [comment_id]

        annotations = []
        if label_ids:
            query_comments = GET_ANNOTATIONS_BY_FILTER(ids, label_ids, user_id)

            annotations = None
            with db_cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query_comments)
                annotations = cur.fetchall()

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
