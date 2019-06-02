from __future__ import print_function

from functools import wraps
from flask import request, jsonify
import jwt

from db import mongo

import sys

def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return {'message' : 'Token is missing.'}, 401

        secrets_coll = mongo.cx["admin"].Secrets
        secret_mongo = secrets_coll.find_one().get('globalSecret')

        try:
            data = jwt.decode(token, secret_mongo) # TODO hide pwd
        except: 
            return {'message' : 'Token is invalid.'}, 401

        users_coll = mongo.cx["admin"].Users
        user_mongo = users_coll.find_one({"user" : data["user"]})

        if not user_mongo or user_mongo["blocked"]:
            return {'message' : 'Access denied.'}, 401

        tokens_coll = mongo.cx["admin"].Tokens
        token_mongo = tokens_coll.find_one({"user" : data["user"]})

        if not token_mongo or not token_mongo["token"] or str(token_mongo["token"], 'utf-8') != token:
            return {'message' : 'The token is invalid because the user is not logged in or the token has been updated.'}, 401

        return func(data, *args, **kwargs)

    return decorated