from http import HTTPStatus

import json
import requests
import sys
from flask_restplus import Resource, Namespace

from auth.token import token_required, TokenData
from config import settings
from db import Database, with_database

ns = Namespace('annotations', description="annotations api")


@ns.route('/<int:comment_id>')
class GetLabel(Resource):
    @with_database
    def get(self, db: Database, comment_id):
        annotations = db.annotations.find_all_by_comment_id(comment_id)
        return list(annotations), HTTPStatus.OK


@ns.route('/<int:comment_id>/<int:label_id>/<int:value>')
class LabelComment(Resource):
    @token_required
    @with_database
    @ns.doc(security='apikey')
    def put(self, db: Database, token_data: TokenData, comment_id, label_id, value):
        user_id = token_data["user_id"]
        value = bool(value)

        # Check Args
        if not db.comments.exists(comment_id):
            return {"msg": f"Comment does not exist"}, HTTPStatus.NOT_FOUND

        if not db.labels.exists(label_id):
            return {"msg": f"Label does not exist"}, HTTPStatus.NOT_FOUND

        if not db.users.exists(user_id):
            return {"msg": f"User does not exist"}, HTTPStatus.NOT_FOUND

        db.annotations.set_annotation_for_user_comment_label(user_id, comment_id, label_id, value)
        db.acc.commit()

        # Trigger new Training?
        annotation_count = db.annotations.count_annotations_on_embedded_comments_for_label(label_id)
        model_sample_count = db.models.current_model_training_sample_count(label_id)

        new_training_samples = annotation_count.num_total - model_sample_count

        # is training in progress?
        training_running = db.models.is_training_active(label_id)

        if not training_running \
                and new_training_samples >= settings.NUMBER_SAMPLES_FOR_NEXT_TRAINING \
                and annotation_count.num_positive >= settings.NUMBER_MIN_SAMPLES_PER_CLASS \
                and annotation_count.num_negative >= settings.NUMBER_MIN_SAMPLES_PER_CLASS:
            label = db.labels.find_by_id(label_id)
            print(f'New training ({label["id"]=}, {label["name"]=}, {label["source_id"]=})', file=sys.stderr)

            # trigger new training
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }

            payload = {
                'source_id': label['source_id'],
                'labelname': label['name'],
                'optimize': False,
                'skip-confidence': False
            }

            requests.post('http://127.0.0.1:5050/classification/classification/update', headers=headers, data=json.dumps(payload))

        return {
            "annotations": annotation_count.num_total,
        }, HTTPStatus.OK
