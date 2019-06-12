from functools import wraps
from flask import request
import jwt

from db import mongo

import sys

data = []

def returnErrorMsg(msg):
    return {'message' : msg}, 401

def checkIfTokenExists(token):
    return token is not None

def checkIfTokenIsValidAndGetData(token):
    secrets_coll = mongo.cx["admin"].Secrets
    secret_mongo = secrets_coll.find_one().get('globalSecret')
    try:
        data = jwt.decode(token, secret_mongo)
    except: 
        return False, None
    return True, data

def checkIfUserIsAuthorised(token, data):
    users_coll = mongo.cx["admin"].Users
    user_mongo = users_coll.find_one({"user" : data["user"]})

    if not user_mongo or user_mongo["blocked"]:
        return False
    return True

def checkIfTheUSerIsLoggedIn(token, data):
        tokens_coll = mongo.cx["admin"].Tokens
        token_mongo = tokens_coll.find_one({"user" : data["user"]})

        if not token_mongo or not token_mongo["token"] or str(token_mongo["token"], 'utf-8') != token:
            return False
        return True

def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.headers['x-access-token'] if 'x-access-token' in request.headers else None
        data = None
        
        if not checkIfTokenExists(token):
            return returnErrorMsg('Token is missing.')

        success, data = checkIfTokenIsValidAndGetData(token)
        if not success:
            return returnErrorMsg('Token is invalid.')

        if not checkIfUserIsAuthorised(token, data):
            return returnErrorMsg('Access denied.')

        #if not checkIfTheUSerIsLoggedIn(token, data):
        #    return returnErrorMsg('The token is invalid because the user is not logged in or the token has been updated.')

        return func(data, *args, **kwargs)

    return decorated