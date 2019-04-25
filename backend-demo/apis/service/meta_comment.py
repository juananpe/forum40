from flask import request
from flask import jsonify
from flask_restplus import Resource, reqparse

from apis.service import api

from db import mongo
from bson.objectid import ObjectId
from bson import json_util

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


def get_comments(meta_label_id):
    comments = mongo.db.Comments
    unlabeled_comments = comments.find({"labels": {"$exists": 1},
                                        "labels.labelId": {"$ne": meta_label_id}},
                                       {"title": 1, "text": 1}).limit(50)
    return unlabeled_comments


@ns.route('/unlabeled')
class UnlabaledGet(Resource):
    def put(self):

        meta_label_id = get_or_create_meta_label()

        unlabeled_comments = get_comments(
            meta_label_id)

        
        # Todo:
        # 1. get all unlabeled comments
        # 2. send unlabeled comments to meta-comment service
        # 3. write classification to database

        return json_util.dumps(unlabeled_comments), 200
