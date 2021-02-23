from http import HTTPStatus

import datetime
import jwt
import wrapt
from flask import request
from typing import TypedDict, Tuple, Optional

from config.settings import JWT_KEY
from db import with_database, Database


class TokenData(TypedDict):
    user: str
    user_id: int
    role: str
    exp: datetime.datetime


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


def check_source_id_access(source_id: int, token: str):
    success, data = check_if_token_is_valid_and_get_data(token)
    return allow_access_source_id(source_id, data)


@with_database
def is_source_id_protected(db: Database, source_id: int):
    return db.sources.find_by_id(source_id)['protected']


def allow_access_source_id(source_id: int, token_data: Optional[TokenData]):
    is_admin = token_data is not None and token_data['role'] == 'admin'
    return is_admin or not is_source_id_protected(source_id)


@wrapt.decorator
def check_source_id(wrapped, instance, args, kwargs):
    source_id = request.args.get('source_id', None)
    if source_id:
        token = request.headers['x-access-token'] if 'x-access-token' in request.headers else None
        if not check_source_id_access(source_id, token):
            return '', HTTPStatus.FORBIDDEN
    return wrapped(*args, **kwargs)


@wrapt.decorator
def token_required(wrapped, instance, args, kwargs):
    token = request.headers['x-access-token'] if 'x-access-token' in request.headers else None

    if not check_if_token_exists(token):
        return '', HTTPStatus.FORBIDDEN

    success, data = check_if_token_is_valid_and_get_data(token)
    if not success:
        return '', HTTPStatus.UNAUTHORIZED

    return wrapped(data, *args, **kwargs)


@wrapt.decorator
def token_optional(wrapped, instance, args, kwargs):
    token = request.headers['x-access-token'] if 'x-access-token' in request.headers else None

    success, data = check_if_token_is_valid_and_get_data(token)

    return wrapped(data, *args, **kwargs)
