from flask import request
from flask_restplus import Resource, reqparse, fields
from apis.db import api

from db import postgres
from db import postgres_json
from db import postgres_con

from db.queries import *

from jwt_auth.token import token_required

ns = api.namespace('annotations', description="annotations api")

@ns.route('/count')
class SourcesCount(Resource):
    def get(self):
        postgres.execute(COUNT_ANNOTATIONS)
        db_return = postgres.fetchone()

        if db_return:
             return {'count': db_return[0]}, 200
        
        return {"msg": "Error"}, 400

@ns.route('/<int:comment_id>')
class GetLabel(Resource):
    def get(self, comment_id):
        postgres_json.execute(f"SELECT label_id, user_id, label FROM Annotations WHERE comment_id = {comment_id}")
        db_return = postgres_json.fetchall()
        return db_return

def _comment_exists(id):
    postgres.execute(SELECT_COMMENT_BY_ID(id))
    db_result = postgres.fetchone()
    return db_result != None

def _label_exists(id):
    postgres.execute(SELECT_LABEL_BY_ID(id))
    db_result = postgres.fetchone()
    return db_result != None

def _user_exists(id):
    postgres.execute(SELECT_USER_BY_ID(id))
    db_result = postgres.fetchone()
    return db_result != None

import sys

@ns.route('/<int:comment_id>/<int:label_id>/<int:user_id>/<int:label>')
class LabelComment(Resource):
    @token_required
    @api.doc(security='apikey')
    def put(self, data, comment_id ,label_id, user_id, label):

        label = bool(label)

        # Check Args
        if not _comment_exists(comment_id):
            return {"msg": "No Comments with id: {0}".format(comment_id)}, 400

        if not _label_exists(label_id):
            return {"msg": "No Label with id: {0}".format(comment_id)}, 400

        if not _user_exists(user_id):
            return {"msg": "No User with id: {0}".format(comment_id)}, 400

        postgres_json.execute(SELECT_LABEL_FROM_ANNOTATIONS_BY_IDS(label_id, comment_id, user_id))
        db_result = postgres_json.fetchone()

        if not db_result: # No Annotation found
            postgres.execute(INSERT_ANNOTATION(label_id, comment_id, user_id, label))
        elif db_result['label'] != label: # Update
            postgres.execute(UPDATE_ANNOTATION(label_id, comment_id, user_id, label))
        else: 
            pass

        postgres_con.commit()

        return "ok", 200