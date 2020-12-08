import json
import requests
import sys
from flask_restplus import Resource, Namespace
from psycopg2.extras import RealDictCursor

from config import settings
from db import postgres_con, db_cursor
from db.queries import *
from jwt_auth.token import token_required

ns = Namespace('annotations', description="annotations api")


@ns.route('/<int:comment_id>')
class GetLabel(Resource):
    def get(self, comment_id):
        query = f"SELECT label_id, user_id, label FROM Annotations WHERE comment_id = {comment_id}"
        db_return = []
        with db_cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            db_return = cur.fetchall()

        return db_return


def _comment_exists(id):
    postgres = postgres_con.cursor()
    postgres.execute(SELECT_COMMENT_BY_ID(id))
    db_result = postgres.fetchone()
    return db_result is not None


def _label_exists(id):
    postgres = postgres_con.cursor()
    postgres.execute(SELECT_LABEL_BY_ID(id))
    db_result = postgres.fetchone()
    return db_result is not None


def _user_exists(id):
    postgres = postgres_con.cursor()
    postgres.execute(SELECT_USER_BY_ID(id))
    db_result = postgres.fetchone()
    return db_result is not None


@ns.route('/<int:comment_id>/<int:label_id>/<int:label>')
class LabelComment(Resource):
    @token_required
    @ns.doc(security='apikey')
    def put(self, data, comment_id, label_id, label):
        user_id = self["user_id"]
        label = bool(label)

        # Check Args
        if not _comment_exists(comment_id):
            return {"msg": f"No Comments with id: {comment_id}"}, 400

        if not _label_exists(label_id):
            return {"msg": f"No Label with id: {label_id}"}, 400

        if not _user_exists(user_id):
            return {"msg": f"No User with id: {user_id}"}, 400

        query = SELECT_LABEL_FROM_ANNOTATIONS_BY_IDS(label_id, comment_id, user_id)

        db_result = []
        with db_cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            db_result = cur.fetchone()

        if not db_result:  # No Annotation found
            with db_cursor() as cur:
                cur.execute(INSERT_ANNOTATION(label_id, comment_id, user_id, label))

        elif db_result['label'] != label:  # Update
            with db_cursor() as cur:
                cur.execute(UPDATE_ANNOTATION(label_id, comment_id, user_id, label))
        else:
            pass

        postgres_con.commit()

        # Trigger new Training?

        with db_cursor() as cur:
            cur.execute(GET_ANNOTATED_COMMENTS(), (label_id,))
            current_pos_annotated_samples, current_neg_annotated_samples = cur.fetchone()
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

            payload = {
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
            "samples_left_for_new_training": samples_left_for_new_training,
            "numbers_pos_samples_missing": 10-current_pos_annotated_samples if current_pos_annotated_samples < 10 else 0,
            "numbers_neg_samples_missing": 10 - current_neg_annotated_samples if current_neg_annotated_samples < 10 else 0
        }, 200
