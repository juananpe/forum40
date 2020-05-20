from flask import request
from flask_restplus import Resource, reqparse, fields
from apis.db import api

from config import settings

from psycopg2.extras import RealDictCursor

from db import postgres_con, db_cursor

from db.queries import *
from psycopg2 import DatabaseError

from jwt_auth.token import token_required

from db.db_models import comments_parser_sl

import sys
import json
import requests

ns = api.namespace('annotations', description="annotations api")

@ns.route('/count')
class SourcesCount(Resource):
    def get(self):
        query = COUNT_ANNOTATIONS

        db_return = []
        with db_cursor() as cur:
            cur.execute(query)
            db_return = cur.fetchone()

        if db_return:
             return {'count': db_return[0]}, 200
        
        return {"msg": "Error"}, 400

@ns.route('/count_facts/')
class SourcesCountF(Resource):
    def get(self):
        query = 'SELECT COUNT(*) FROM facts'
        db_return = []
        with db_cursor() as cur:
            cur.execute(query)
            db_return = cur.fetchone()

        if db_return:
             return {'count': db_return[0]}, 200
        
        return {"msg": "Error"}, 400

@ns.route('/<int:comment_id>')
class GetLabel(Resource):
    def get(self, comment_id):
        
        query = f"SELECT label_id, user_id, label FROM Annotations WHERE comment_id = {comment_id}"
        db_return = []
        with db_cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            db_return = cur.fetchall()

        return db_return


@ns.route('/user/<int:user_id>')
@api.expect(comments_parser_sl)
class GetLabelUser(Resource):
    def get(self, user_id):

        args = comments_parser_sl.parse_args()
        skip = args["skip"]
        limit = args["limit"]

        annotations_where_sec = ''
        if 'label' in args and args['label']:
            labelIds = ' WHERE label_id IN ({0})'.format(", ".join(i for i in args['label']))
            annotations_where_sec += labelIds

        comments_where_sec = ''
        if 'keyword' in args and args['keyword']:
            searchwords = ' OR '.join("text LIKE '%{0}%'".format(x) for x in args['keyword'])
            comments_where_sec += 'WHERE ' +  searchwords

        query = f"""
            SELECT _.id, array_agg(_.agg) as group_annotation FROM
            (
                SELECT c.id, ARRAY[a.label_id, a.label::int] as agg
                    FROM (SELECT * FROM comments {comments_where_sec} LIMIT {limit} OFFSET {skip}) AS c 
                    LEFT OUTER JOIN 
                    (SELECT * FROM annotations {annotations_where_sec}) AS a
                    ON c.id = a.comment_id
                    WHERE a.user_id = '{user_id}'
                    GROUP BY c.id, a.label_id, a.label
            ) _ 
            GROUP BY _.id
        """
        db_return = []
        with db_cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            db_return = cur.fetchall()
        return db_return


@ns.route('/group/')
@api.expect(comments_parser_sl)
class GetLabelGroup(Resource):
    def get(self):

        args = comments_parser_sl.parse_args()
        skip = args["skip"]
        limit = args["limit"]

        annotations_where_sec = ''
        if 'label' in args and args['label']:
            labelIds = ' WHERE label_id IN ({0})'.format(", ".join(i for i in args['label']))
            annotations_where_sec += labelIds

        comments_where_sec = ''
        if 'keyword' in args and args['keyword']:
            searchwords = ' OR '.join("text LIKE '%{0}%'".format(x) for x in args['keyword'])
            comments_where_sec += 'WHERE ' +  searchwords

        query = f"""
        SELECT _.id, _.title, _.text, _.timestamp, array_agg(_.agg) as group_annotation FROM
        (
            SELECT c.id, c.title, c.text, c.timestamp, ARRAY[a.label_id, count(a.label or null), count(not a.label or null)] as agg
                FROM (SELECT * FROM comments {comments_where_sec} LIMIT {limit} OFFSET {skip}) AS c 
                LEFT OUTER JOIN 
                (SELECT * FROM annotations {annotations_where_sec}) AS a
                ON c.id = a.comment_id
                GROUP BY c.id, a.label_id, c.title, c.text, c.timestamp
        ) _ 
        GROUP BY _.id, _.title, _.text, _.timestamp
        """

        db_return = []
        with db_cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            db_return = cur.fetchall()

        return db_return

def _comment_exists(id):
    postgres = postgres_con.cursor()
    postgres.execute(SELECT_COMMENT_BY_ID(id))
    db_result = postgres.fetchone()
    return db_result != None

def _label_exists(id):
    postgres = postgres_con.cursor()
    postgres.execute(SELECT_LABEL_BY_ID(id))
    db_result = postgres.fetchone()
    return db_result != None

def _user_exists(id):
    postgres = postgres_con.cursor()
    postgres.execute(SELECT_USER_BY_ID(id))
    db_result = postgres.fetchone()
    return db_result != None

@ns.route('/<int:comment_id>/<int:label_id>/<int:label>')
class LabelComment(Resource):
    @token_required
    @api.doc(security='apikey')
    def put(self, data, comment_id ,label_id, label):
        user_id = self["user_id"]
        label = bool(label)

        # Check Args
        if not _comment_exists(comment_id):
            return {"msg": "No Comments with id: {0}".format(comment_id)}, 400

        if not _label_exists(label_id):
            return {"msg": "No Label with id: {0}".format(label_id)}, 400

        if not _user_exists(user_id):
            return {"msg": "No User with id: {0}".format(user_id)}, 400

        query = SELECT_LABEL_FROM_ANNOTATIONS_BY_IDS(label_id, comment_id, user_id)

        db_result = []
        with db_cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            db_result = cur.fetchone()

        if not db_result: # No Annotation found
            with db_cursor() as cur:
                cur.execute(INSERT_ANNOTATION(label_id, comment_id, user_id, label))

        elif db_result['label'] != label: # Update
            with db_cursor() as cur:
                cur.execute(UPDATE_ANNOTATION(label_id, comment_id, user_id, label))
        else: 
            pass

        postgres_con.commit()

        # Trigger new Training?

        with db_cursor() as cur:
            cur.execute(GET_ANNOTATED_COMMENTS(), (label_id,))
            current_pos_annotated_samples,current_neg_annotated_samples = cur.fetchone()
            current_annotated_samples = current_pos_annotated_samples + current_neg_annotated_samples


        # get number training samples of previous model
        with db_cursor() as cur:
            cur.execute(GET_PREVIOUS_NUMBER_TRAINING_SAMPLES(), (label_id,))
            result = cur.fetchone()
            if result:
                previous_number_training_samples = result[0]
            else:
                previous_number_training_samples = 0
            
        new_training_samples = current_annotated_samples - previous_number_training_samples

        # is training in progress?
        with db_cursor() as cur:
            cur.execute(GET_RUNNING_TRAINING(), (label_id,))
            training_runnninng = cur.fetchone()[0]

        triggered_training = False

        # trigger training check
        if not training_runnninng \
        and new_training_samples >= settings.NUMBER_SAMPLES_FOR_NEXT_TRAINING \
        and current_pos_annotated_samples >= 10 \
        and current_neg_annotated_samples >= 10:
            print(f'New training for label_id {label_id}', file=sys.stderr)

            with db_cursor() as cur:
                cur.execute(GET_LABEL_INFO(), (label_id,))
                label_name, source_id = cur.fetchone()
                print(f"label_name: {label_name}, source_id: {source_id}", file=sys.stderr)

            # trigger new training
            headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
            }

            payload={
                "source_id": source_id,
                "labelname": label_name,
                "optimize": False,
                "skip-confidence": False
            }

            response = requests.post('http://127.0.0.1:5050/classification/classification/update', headers=headers, data=json.dumps(payload))

            print(response.text, file=sys.stderr)

            triggered_training = True

        # add number left for new training
        samples_left_for_new_training = settings.NUMBER_SAMPLES_FOR_NEXT_TRAINING - new_training_samples

        return {
            "annotations": current_annotated_samples,
            "triggered_training": triggered_training,
            "training_running": training_runnninng,
            "samples_left_for_new_training":samples_left_for_new_training,
            "numbers_pos_samples_missing":10-current_pos_annotated_samples if current_pos_annotated_samples < 10 else 0,
            "numbers_neg_samples_missing": 10 - current_neg_annotated_samples if current_neg_annotated_samples < 10 else 0
        }, 200