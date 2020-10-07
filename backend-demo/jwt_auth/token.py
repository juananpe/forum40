from functools import wraps
from flask import request
import jwt

from db import postgres_con
import sys

globalSecret = "eh9Df9G27gahgHJ7g2oGQz6Ug5he6ud5shd" # TODO hide

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


def check_source_id_access(source_id, token):
    success, data = checkIfTokenIsValidAndGetData(token)
    if success:
        role = data.get('role', '')
        if role == 'admin':
            return True

    return not is_source_id_protected(source_id)


def is_source_id_protected(source_id):
    postgres = postgres_con.cursor()
    postgres.execute("SELECT protected FROM sources WHERE id=%s", (source_id,))
    db_result = postgres.fetchone()
    isProtected = db_result[0]
    return isProtected

def allow_access_source_id(source_id, token_dict):
    is_protected = is_source_id_protected(source_id)
    if is_protected:
        role = None
        if token_dict:
            role = token_dict.get('role', None)
            return role == 'admin'
        else:
            return False
    return True



def check_source_id(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        source_id = request.args.get('source_id', None)
        if source_id:
            token = request.headers['x-access-token'] if 'x-access-token' in request.headers else None
            if not check_source_id_access(source_id, token):
                return returnErrorMsg('Cannot access source_id.')
        return func(*args, **kwargs)
    return decorated



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