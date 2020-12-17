import jwt
from flask import request
from functools import wraps

from db import postgres_con

globalSecret = "eh9Df9G27gahgHJ7g2oGQz6Ug5he6ud5shd"  # TODO hide


def returnErrorMsg(msg):
    return {'message': msg}, 401


def checkIfTokenExists(token):
    return token is not None


def checkIfTokenIsValidAndGetData(token):
    try:
        return True, jwt.decode(token, globalSecret)
    except:
        return False, None


def create_token(user_id: int, user_name: str, user_role: str) -> str:
    return jwt.encode({
        'user': user_name,
        'user_id': user_id,
        'role': user_role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)},
        globalSecret
    ).decode('UTF-8')


def checkIfUserIsAuthorised(token, data):
    postgres = postgres_con.cursor()
    postgres.execute("SELECT COUNT(*) FROM users WHERE name = '{0}';".format(data["user"]))
    db_result = postgres.fetchone()

    if not db_result or db_result == 0:
        return False
    return True


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

        if not checkIfTokenExists(token):
            return returnErrorMsg('Token is missing.')

        success, data = checkIfTokenIsValidAndGetData(token)
        if not success:
            return returnErrorMsg('Token is invalid.')

        if not checkIfUserIsAuthorised(token, data):
            return returnErrorMsg('Access denied.')

        return func(data, *args, **kwargs)

    return decorated


def token_optional(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.headers['x-access-token'] if 'x-access-token' in request.headers else None

        success, data = checkIfTokenIsValidAndGetData(token)

        return func(data, *args, **kwargs)

    return decorated
