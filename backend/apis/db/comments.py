from collections import defaultdict
from http import HTTPStatus

import dateutil.rrule as rrule
from datetime import date, datetime
from flask import request
from flask_restplus import Resource, Namespace, inputs
from typing import List, Dict, Optional, Iterable, Tuple

from apis.service.colibert_client import CoLiBertClient
from apis.utils.transformation import slice_dicts
from auth.token import token_optional, check_source_id, allow_access_source_id, TokenData
from auth.token import token_required
from db import with_database, Database
from db.db_models import comments_parser_sl, comment_parser_post, comments_list_parser, \
    group_by_model, comment_parser
from db.repositories.comments import TimestampSorting, Order, FactSorting, UncertaintyOrder, \
    Granularity, comment_fields
from embeddings.utils import concat

ns = Namespace('comments', description="comments api")
min_date = date(2016, 6, 1)


@ns.route('/')
class CommentsGet(Resource):
    @check_source_id
    @token_optional
    @with_database
    @ns.doc(security='apikey')
    @ns.expect(comments_parser_sl)
    def get(self, db: Database, token_data: Optional[TokenData]):
        args = comments_parser_sl.parse_args()

        if (label_sort_id := args['label_sort_id']) is None:
            sorting = TimestampSorting(Order.desc)
        else:
            order_num = args['order']
            sort_order = [UncertaintyOrder, Order.asc, Order.desc][order_num]
            sorting = FactSorting(label_sort_id, order=sort_order)

        comments = list(db.comments.find_all_by_query(
            source_id=args['source_id'],
            keywords=args['keyword'],
            sorting=sorting,
            document_category=args['category'],
            limit=args["limit"],
            offset=args["skip"],
            fields=comment_fields(content=True, metadata=True),
        ))
        load_annotations(
            db=db,
            comments=comments,
            label_ids=args['label'],
            user_id=token_data['user_id'] if token_data is not None else None,
        )

        return comments

    @check_source_id
    @token_required
    @with_database
    @ns.doc(security='apikey')
    @ns.expect(comment_parser_post)
    def post(self, db: Database, token_data: TokenData):
        args = comment_parser_post.parse_args()
        source_id = args['source_id']
        external_id = args['external_id']

        ext_id_fields = {'source_id': source_id, 'external_id': external_id}

        if (id_ := db.comments.find_id_by_external_id(source_id, external_id)) is not None:
            return {'id': id_} | ext_id_fields, HTTPStatus.CONFLICT

        id_ = db.comments.insert(args)
        return {'id': id_} | ext_id_fields, HTTPStatus.OK


@ns.route('/json')
class CommentsInsertMany(Resource):
    @token_optional
    @with_database
    @ns.doc(security='apikey')
    @ns.expect(comments_list_parser)
    def post(self, db: Database, token_data: Optional[TokenData]):
        comments = request.json
        for comment in comments:
            comment['timestamp'] = inputs.datetime_from_iso8601(comment['timestamp'])

        ids = db.comments.insert_many(comments)
        return {'ids': ids}, HTTPStatus.OK


@check_source_id
@ns.route('/time_histogram')
@ns.expect(group_by_model)
class CommentsGrouped(Resource):
    @with_database
    def get(self, db: Database):
        args = group_by_model.parse_args()
        granularity, recurrence_frequency, dtf = {
            'day': (Granularity.DAY, rrule.DAILY, '%d.%m.%Y'),
            'month': (Granularity.MONTH, rrule.MONTHLY, '%m.%Y'),
            'year': (Granularity.YEAR, rrule.YEARLY, '%Y'),
        }[args['granularity']]

        db_result = db.comments.count_by_timestamp_query(
            granularity=granularity,
            source_id=args['source_id'],
            label_id=args['label'],
            keywords=args['keyword'],
        )
        count_by_date = defaultdict(
            lambda: 0,
            {date(d['year'], d.get('month', 1), d.get('day', 1)).strftime(dtf): d['count'] for d in db_result},
        )

        now = datetime.now()
        start_dt = db.comments.find_first_timestamp_by_source(args['source_id']) or now
        end_dt = now
        dt_range = rrule.rrule(recurrence_frequency, dtstart=start_dt, until=end_dt)

        return {'start_time': {'year': start_dt.year, 'month': start_dt.month, 'day': start_dt.day}} \
            | slice_dicts([{'time': dt.strftime(dtf), 'data': count_by_date[dt.strftime(dtf)]} for dt in dt_range])


@ns.route('/parent_recursive/<string:id>/')
class CommentsParentRec(Resource):

    @token_optional
    @with_database
    @ns.doc(security='apikey')
    def get(self, db: Database, token_data: Optional[TokenData], id):
        comments = list(db.comments.find_all_parents(id))

        if len(comments) == 0:
            return '', HTTPStatus.NOT_FOUND
        elif not allow_access_source_id(comments[0]['source_id'], token_data):
            return '', HTTPStatus.FORBIDDEN

        return {
            "comments": list(reversed(comments)),
            "size": len(comments)
        }


@ns.route('/<int:comment_id>/')
@ns.expect(comment_parser)
class Comment(Resource):
    @token_optional
    @with_database
    @ns.doc(security='apikey')
    def get(self, db: Database, token_data: TokenData, comment_id):
        args = comment_parser.parse_args()

        comment = db.comments.find_by_id(comment_id, fields=comment_fields(content=True, metadata=True))
        if not allow_access_source_id(comment['source_id'], token_data):
            return '', HTTPStatus.FORBIDDEN

        load_annotations(
            db=db,
            comments=[comment],
            label_ids=args['label'],
            user_id=token_data['user_id'] if token_data else None,
        )

        return comment


@ns.route('/<int:comment_id>/document')
class CommentArticle(Resource):
    @token_optional
    @with_database
    @ns.doc(securits='apikey')
    def get(self, db: Database, token_data: TokenData, comment_id: int):
        comment = db.comments.find_by_id(comment_id, fields={'source_id', 'doc_id', 'title', 'text'})
        comment_full_text = concat(comment['title'], comment['text'])
        if not allow_access_source_id(comment['source_id'], token_data):
            return '', HTTPStatus.FORBIDDEN

        doc = db.documents.find_by_id(comment['doc_id'], fields={'url', 'title', 'text'})
        paragraph_contents = doc.pop('text').split('\n')
        scores = CoLiBertClient().score_all_pairs(
            queries=[comment_full_text],
            contexts=paragraph_contents,
        )

        doc['paragraphs'] = [
            {'content': content, 'link_score': score}
            for content, score in zip(paragraph_contents, scores[0])
        ]

        return doc


def load_annotations(db: Database, comments: List[Dict], label_ids: List[int], user_id: Optional[int] = None):
    if len(comments) == 0 or len(label_ids) == 0:
        return

    comment_ids = [comment['id'] for comment in comments]

    def key_by(items: Iterable[Dict]) -> Dict[Tuple[int, int], Optional[Dict]]:
        return defaultdict(
            lambda: None,
            {(item['comment_id'], item['label_id']): item for item in items}
        )

    facts = key_by(db.facts.find_by_comment_and_labels(comment_ids, label_ids))
    annotations = key_by(db.annotations.count_by_value_for_comments(comment_ids, label_ids))
    if user_id is None:
        user_annotations = defaultdict(lambda: None)
    else:
        user_annotations = key_by(db.annotations.find_by_user_for_comments(user_id, comment_ids, label_ids))

    for comment in comments:
        comment['annotations'] = []
        for label_id in label_ids:
            agg = {'label_id': label_id}
            comment['annotations'].append(agg)

            if (annotation := annotations[(comment['id'], label_id)]) is not None:
                agg |= {
                    'group_count_true': annotation['count_true'],
                    'group_count_false': annotation['count_false'],
                }
            else:
                agg |= {'group_count_true': 0, 'group_count_false': 0}

            if (fact := facts[(comment['id'], label_id)]) is not None:
                agg |= {'ai': fact['label'], 'ai_pred': fact['confidence']}
            else:
                agg |= {'ai': None, 'ai_pred': None}

            if (user_annotation := user_annotations[(comment['id'], label_id)]) is not None:
                agg |= {'user': user_annotation['label']}
            else:
                agg |= {'user': None}
