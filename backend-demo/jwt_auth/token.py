from http import HTTPStatus

from typing import TypedDict, Tuple, Optional

import datetime
import jwt
import wrapt
from flask import request

from config.settings import JWT_KEY
from db import postgres_con


class TokenData(TypedDict):
    user: str
    user_id: int
    role: str
    exp: datetime.datetime


def return_error_msg(msg):
    return {'message': msg}, HTTPStatus.UNAUTHORIZED


def check_if_token_exists(token):
    return token is not None


def check_if_token_is_valid_and_get_data(token: str) -> Tuple[bool, Optional[TokenData]]:
    try:
        return True, jwt.decode(token, JWT_KEY)
    except:
        return False, None


def create_token(user_id: int, user_name: str, user_role: str) -> str:
    return jwt.encode(TokenData(
        user=user_name,
        user_id=user_id,
        role=user_role,
        exp=datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
    ), JWT_KEY).decode('UTF-8')


def check_if_user_is_authorised(token, data):
    postgres = postgres_con.cursor()
    postgres.execute("SELECT COUNT(*) FROM users WHERE name = %s", (data["user"],))
    db_result = postgres.fetchone()

    if not db_result or db_result == 0:
        return False
    return True


def check_source_id_access(source_id, token):
    success, data = check_if_token_is_valid_and_get_data(token)
    if success:
        role = data.get('role', '')
        if role == 'admin':
            return True

    return not is_source_id_protected(source_id)


def is_source_id_protected(source_id):
    postgres = postgres_con.cursor()
    postgres.execute("SELECT protected FROM sources WHERE id=%s", (source_id,))
    db_result = postgres.fetchone()
    is_protected = db_result[0]
    return is_protected


def allow_access_source_id(source_id, token_data: Optional[TokenData]):
    is_admin = token_data is not None and token_data
    return is_admin or not is_source_id_protected(source_id)


@wrapt.decorator
def check_source_id(wrapped, instance, args, kwargs):
    source_id = request.args.get('source_id', None)
    if source_id:
        token = request.headers['x-access-token'] if 'x-access-token' in request.headers else None
        if not check_source_id_access(source_id, token):
            return return_error_msg('Cannot access source_id.')
    return wrapped(*args, **kwargs)


@wrapt.decorator
def token_required(wrapped, instance, args, kwargs):
    token = request.headers['x-access-token'] if 'x-access-token' in request.headers else None

    if not check_if_token_exists(token):
        return return_error_msg('Token is missing.')

    success, data = check_if_token_is_valid_and_get_data(token)
    if not success:
        return return_error_msg('Token is invalid.')

    if not check_if_user_is_authorised(token, data):
        return return_error_msg('Access denied.')

    return wrapped(data, *args, **kwargs)


@wrapt.decorator
def token_optional(wrapped, instance, args, kwargs):
    token = request.headers['x-access-token'] if 'x-access-token' in request.headers else None

    success, data = check_if_token_is_valid_and_get_data(token)

    return wrapped(data, *args, **kwargs)
