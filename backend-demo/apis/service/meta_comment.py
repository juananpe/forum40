from flask import request
from flask import jsonify
from flask_restplus import Resource
import requests
from apis.service import api
import json
from db import mongo
from bson.objectid import ObjectId
from bson import json_util
from pymongo import UpdateOne

ns = api.namespace('classification', description="Classify unlabeled comments")


def get_or_create_meta_label() -> ObjectId:
    comments = mongo.db.Comments
    labels = mongo.db.Labels
    meta_label = list(labels.find({'classname': 'meta'}))
    if not meta_label:
        meta_label_id = labels.insert_one({"type": "binary",
                                           "classname": [
                                               "meta",
                                               "non-meta"
                                           ],
                                           "description": "meta-comment",
                                           "scale": "ordinal",
                                           "staffId": ""}).inserted_id
    else:
        meta_label_id = meta_label[0].get('_id')

    return meta_label_id


def get_comments(meta_label_id, number=50):
    comments = mongo.db.Comments
    unlabeled_comments = comments.find({"labels": {"$exists": 1},
                                        "labels.labelId": {"$ne": meta_label_id}},
                                       {"title": 1, "text": 1}).limit(number)
    return unlabeled_comments


def classify_comments(comments):
    r = requests.post('http://meta:5060/comments', json={'comments': comments})
    return r.text


def create_update_operation(_id, result, label_id):

    label = {
        "labelId": label_id,
        "classified": result['confidence'].index(max(result['confidence'])),
        "confidence": result['confidence'],
        "manualLabels": []
    }

    updateStatement = {
        '$push': {
            "labels": label
        }
    }

    return UpdateOne({'_id': _id}, updateStatement)


def update_comments(ids, results, label_id):
    comments = mongo.db.Comments
    updates = [create_update_operation(
        _id, result, label_id) for _id, result in zip(ids, results)]
    write_result = comments.bulk_write(updates).bulk_api_result
    return write_result


@ns.route('/unlabeled')
class UnlabaledGet(Resource):
    def put(self):

        meta_label_id = get_or_create_meta_label()
        number_updates = 0

        while True:
            unlabeled_comments = list(get_comments(meta_label_id, number=200))
            if not unlabeled_comments:
                break

            unlabeled_comment_ids = [c.pop('_id') for c in unlabeled_comments]

            results = json.loads(classify_comments(unlabeled_comments))

            update_result = update_comments(
                unlabeled_comment_ids, results, meta_label_id)

            number_updates += update_result['nModified']

        return {'updated': number_updates}, 200
