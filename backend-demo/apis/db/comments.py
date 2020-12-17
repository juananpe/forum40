from collections import defaultdict

from datetime import timedelta, date
from dateutil.relativedelta import relativedelta
from flask import request
from flask_restplus import Resource, Namespace, inputs
from typing import List, Dict, Optional, Iterable, Tuple

from db import with_database, Database
from db.db_models import comments_parser_sl, comment_parser_post, comments_list_parser, \
    groupByModel, comment_parser
from db.repositories.comments import TimestampSorting, Order, FactSorting, UncertaintyOrder, \
    Granularity, comment_fields
from jwt_auth.token import token_optional, check_source_id, allow_access_source_id
from jwt_auth.token import token_required

ns = Namespace('comments', description="comments api")
min_date = date(2016, 6, 1)


@ns.route('/')
class CommentsGet(Resource):
    @check_source_id
    @token_optional
    @ns.doc(security='apikey')
    @ns.expect(comments_parser_sl)
    @with_database
    def get(self, db: Database, data):
        # get args
        args = comments_parser_sl.parse_args()

        if (label_sort_id := args.get('label_sort_id', None)) is None:
            sorting = TimestampSorting(Order.desc)
        else:
            order = args.get('order', None)
            sort_order = [UncertaintyOrder, Order.asc, Order.desc][order]
            sorting = FactSorting(label_sort_id, order=sort_order)

        comments = list(db.comments.find_all_by_query(
            source_id=args.get('source_id', None),
            keywords=args.get('keyword', []),
            sorting=sorting,
            document_category=args.get('category', None),
            limit=args["limit"],
            offset=args["skip"],
            fields=comment_fields(content=True, metadata=True),
        ))
        load_annotations(
            db=db,
            comments=comments,
            label_ids=args.get('label', []),
            user_id=self['user_id'] if self else None,
        )

        return comments

    @check_source_id
    @ns.doc(security='apikey')
    @ns.expect(comment_parser_post)
    @token_required
    @with_database
    def post(self, db: Database, data):
        args = comment_parser_post.parse_args()
        source_id = args['source_id']
        external_id = args['external_id']

        ext_id_fields = {'source_id': source_id, 'external_id': external_id}

        if (id_ := db.comments.find_id_by_external_id(source_id, external_id)) is not None:
            return {'id': id_} | ext_id_fields, 409

        id_ = db.comments.insert(args)
        return {'id': id_} | ext_id_fields, 200


@ns.route('/json')
class CommentsInsertMany(Resource):
    @token_optional
    @ns.doc(security='apikey')
    @ns.expect(comments_list_parser)
    @with_database
    def post(self, db: Database, data):
        comments = request.json
        for comment in comments:
            comment['timestamp'] = inputs.datetime_from_iso8601(comment['timestamp'])

        ids = db.comments.insert_many(comments)
        return {'ids': ids}, 200


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


@check_source_id
@ns.route('/groupByDay')
@ns.expect(groupByModel)
class CommentsGroupByDay(Resource):
    @with_database
    def get(self, db: Database):
        args = groupByModel.parse_args()

        db_result = list(db.comments.count_by_timestamp_query(
            granularity=Granularity.MONTH,
            source_id=args['source_id'],
            label_id=args['label'],
            keywords=args['keywords'],
        ))

        return prepareForVisualisation(addMissingDays(db_result), lambda d: f"{d['day']}.{d['month']}.{d['year']}")


@check_source_id
@ns.route('/groupByMonth')
@ns.expect(groupByModel)
class CommentsGroupByMonth(Resource):
    @with_database
    def get(self, db: Database):
        args = groupByModel.parse_args()

        db_result = list(db.comments.count_by_timestamp_query(
            granularity=Granularity.MONTH,
            source_id=args['source_id'],
            label_id=args['label'],
            keywords=args['keywords'],
        ))

        return prepareForVisualisation(addMissingMonths(db_result), lambda d: f"{d['month']}.{d['year']}")


@check_source_id
@ns.route('/groupByYear')
@ns.expect(groupByModel)
class CommentsGroupByYear(Resource):
    @with_database
    def get(self, db: Database):
        args = groupByModel.parse_args()

        db_result = list(db.comments.count_by_timestamp_query(
            granularity=Granularity.MONTH,
            source_id=args['source_id'],
            label_id=args['label'],
            keywords=args['keywords'],
        ))

        return prepareForVisualisation(addMissingYears(db_result), lambda d: f"{d['year']}")


@ns.route('/parent_recursive/<string:id>/')
class CommentsParentRec(Resource):

    @token_optional
    @ns.doc(security='apikey')
    @with_database
    def get(self, db: Database, data, id):
        comments = list(db.comments.find_all_parents(id))

        if len(comments) == 0:
            return '', 404
        elif not allow_access_source_id(comments[0]['source_id'], self):
            return '', 401

        return {
            "comments": reversed([c | {'timestamp': c['timestamp'].isoformat()} for c in comments]),
            "size": len(comments)
        }


@ns.route('/<int:comment_id>/')
@ns.expect(comment_parser)
class Comment(Resource):
    @token_optional
    @ns.doc(security='apikey')
    @with_database
    def get(self, db: Database, request, comment_id):
        args = comment_parser.parse_args()

        comment = db.comments.find_by_id(comment_id, fields=comment_fields(content=True, metadata=True))
        if not allow_access_source_id(comment['source_id'], self):
            return '', 401

        load_annotations(
            db=db,
            comments=[comment],
            label_ids=args['label'] if 'label' in args else [],
            user_id=self['user_id'] if self else None,
        )

        return comment


def load_annotations(db: Database, comments: List[Dict], label_ids: List[int], user_id: Optional[int] = None):
    comment_ids = [comment['id'] for comment in comments]

    def key_by(items: Iterable[Dict]) -> Dict[Tuple[int, int], Optional[Dict]]:
        return defaultdict(
            lambda: None,
            {(item['comment_id'], item['label_id']): item for item in items}
        )

    facts = key_by(db.facts.find_by_comment_and_labels(comment_ids, label_ids))
    annotations = key_by(db.annotations.count_by_value_for_comments(comment_ids, label_ids))
    user_annotations = {} if user_id is None else key_by(db.annotations.find_by_user_for_comments(user_id, comment_ids, label_ids))

    for comment in comments:
        comment['annotations'] = []
        for label_id in label_ids:
            annotation = annotations[(comment['id'], label_id)]
            agg = {
                'label_id': label_id,
                'group_count_true': annotation['count_true'],
                'group_count_false': annotation['count_false']
            }
            comment['annotations'].append(agg)

            if (fact := facts[(comment['id'], label_id)]) is not None:
                agg |= {'ai': fact['label'], 'ai_pred': fact['confidence']}
            else:
                agg |= {'ai': None, 'ai_pred': None}

            if (user_annotation := user_annotations[(comment['id'], label_id)]) is not None:
                agg |= {'user': user_annotation['label']}
            else:
                agg |= {'user': None}
