from flask import jsonify, make_response
from flask_restplus import Resource, Namespace

from db import with_database, Database
from jwt_auth.token import token_required, create_token

ns = Namespace('auth', description="auth api")


@ns.route('/test')
class AuthTest(Resource):
    @token_required
    @ns.doc(security='apikey')
    def get(self, data):
        user = self["user"]

        return {"ok": user}, 200


@ns.route('/login/<string:username>/<string:password>')
class AuthLogin(Resource):
    @with_database
    def get(self, db: Database, username, password):
        user = db.users.find_by_name(username)

        if user is None or user['password'] is None or user['password'] != password:
            return make_response('Wrong username or password', 401)

        return jsonify({
            'user': user['name'],
            'user_id': user['id'],
            'token': create_token(
                user_id=user['id'],
                user_name=user['name'],
                user_role=user['role'],
            ),
        })


@ns.route('/refreshToken/')
class AuthRefresh(Resource):
    @token_required
    @ns.doc(security='apikey')
    def get(self, data):
        user = self["user"]
        user_id = self["user_id"]

        return jsonify({
            'user': user,
            'user_id': user_id,
            'token': create_token(
                user_id=user_id,
                user_name=user,
                user_role=user['role'],
            ),
        })
