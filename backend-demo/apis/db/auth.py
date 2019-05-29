from flask import request, jsonify, Response, make_response
from flask_restplus import Resource, reqparse

from apis.db import api
from models.db_models import aggregate_model, label_time_model, comments_model

from db import mongo
from db.mongo_util import aggregate

from db.queries.comments_label_by_time import get as clbt
from bson import json_util, ObjectId

import json

from jwt_auth.token import token_required

ns = api.namespace('auth', description="auth api")

import jwt
import datetime

from werkzeug.security import generate_password_hash, check_password_hash

# TODO mongo
fake_mongo_DB = {
    "user1" : "22880",
    "user2" : "0815"
}

@ns.route('/test')
class Auth2(Resource):
    @token_required
    @api.doc(security='apikey')
    def get(self):
        return "ok"

@ns.route('/login/<string:username>/<string:password>')
class Auth3(Resource):
    def get(self, username, password):

        if username and password == fake_mongo_DB.get(username) == password: # TODO sec check
            token = jwt.encode({
                'user' : username, 
                'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=60)}, 
                'eh9Df9G27gahgHJ7g2oGQz6Ug5he6ud5shd') # TODO hide pwd
            return jsonify({'token' : token.decode('UTF-8'), 'user' : username})

        return make_response('Could verify', 401, {"WWW-Authenticate" : "Basic realm='Login Required'"})


