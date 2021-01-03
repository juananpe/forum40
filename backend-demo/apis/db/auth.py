from http import HTTPStatus

from flask import jsonify
from flask_restplus import Resource, Namespace, reqparse
from typing import Dict

from auth.authentication import login
from auth.passwords import hash_password
from auth.token import token_required, create_token, TokenData
from db import with_database, Database

ns = Namespace('auth', description="auth api")


@ns.route('/test')
class AuthTest(Resource):
    @token_required
    @ns.doc(security='apikey')
    def get(self, token_data: TokenData):
        user = token_data["user"]

        return {"ok": user}, HTTPStatus.OK


@ns.route('/login/<string:username>/<string:password>')
class AuthLogin(Resource):
    def get(self, username, password):
        user = login(username, password)
        if user is None:
            return 'Wrong username or password', HTTPStatus.UNAUTHORIZED

        return make_auth_response(user)


register_model = reqparse.RequestParser()
register_model.add_argument('name', type=str, required=True)
register_model.add_argument('password', type=str, required=True)


@ns.route('/register/')
class Register(Resource):
    @with_database
    @ns.expect(register_model)
    def post(self, db: Database):
        body = register_model.parse_args()
        id_ = db.users.insert_user(body | {'password': hash_password(body['password'])})
        user = db.users.find_by_id(id_)
        return make_auth_response(user)


@ns.route('/refreshToken/')
class AuthRefresh(Resource):
    @token_required
    @with_database
    @ns.doc(security='apikey')
    def get(self, db: Database, token_data: TokenData):
        user = db.users.find_by_id(token_data['user_id'])
        return make_auth_response(user)


def make_auth_response(user: Dict) -> str:
    return jsonify({
        'user': user['name'],
        'user_id': user['id'],
        'token': create_token(
            user_id=user['id'],
            user_name=user['name'],
            user_role=user['role'],
        ),
    })
