from functools import wraps
from flask import request
import jwt

from db import postgres_con

globalSecret = "eh9Df9G27gahgHJ7g2oGQz6Ug5he6ud5shd" # TODO hide

import sys

def returnErrorMsg(msg):
    return {'message' : msg}, 401

def checkIfTokenExists(token):
    return token is not None

def checkIfTokenIsValidAndGetData(token):
    try:
        return True, jwt.decode(token, globalSecret)
    except: 
        return False, None

def checkIfUserIsAuthorised(token, data):
    postgres = postgres_con.cursor()
    postgres.execute("SELECT COUNT(*) FROM users WHERE name = '{0}';".format(data["user"]))
    db_result = postgres.fetchone()

    if not db_result or db_result == 0:
        return False
    return True

"""def checkIfTheUSerIsLoggedIn(token, data):
        tokens_coll = mongo.cx["admin"].Tokens
        token_mongo = tokens_coll.find_one({"user" : data["user"]})

        if not token_mongo or not token_mongo["token"] or str(token_mongo["token"], 'utf-8') != token:
            return False
        return True
"""

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


def token_optional(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.headers['x-access-token'] if 'x-access-token' in request.headers else None
        data = None

        success, data = checkIfTokenIsValidAndGetData(token)

        return func(data, *args, **kwargs)

    return decorated