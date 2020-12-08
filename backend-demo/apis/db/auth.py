import datetime
import jwt
from flask import jsonify, make_response
from flask_restplus import Resource, Namespace

from db import postgres_con
from db.queries import SELECT_PASSWORD_BY_NAME
from jwt_auth.token import token_required

ns = Namespace('auth', description="auth api")

globalSecret = "eh9Df9G27gahgHJ7g2oGQz6Ug5he6ud5shd"  # TODO hide


@ns.route('/test')
class AuthTest(Resource):
    @token_required
    @ns.doc(security='apikey')
    def get(self, data):
        user = self["user"]

        return {"ok": user}, 200


@ns.route('/login/<string:username>/<string:password>')
class AuthLogin(Resource):
    def get(self, username, password):
        postgres = postgres_con.cursor()
        postgres.execute(SELECT_PASSWORD_BY_NAME, (username,))
        db_result = postgres.fetchone()

        if not db_result or db_result[0] != password or password is None:
            return make_response('Could not verify!', 401)
        else:
            user_id = db_result[1]
            role = db_result[2]
            token = jwt.encode({
                'user': username,
                'user_id': user_id,
                'role': role,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)},
                globalSecret
            )
            return jsonify({'token': token.decode('UTF-8'), 'user': username, 'user_id': user_id})


@ns.route('/refreshToken/')
class AuthRefresh(Resource):
    @token_required
    @ns.doc(security='apikey')
    def get(self, data):
        user = self["user"]
        user_id = self["user_id"]

        token = jwt.encode({
            'user': user,
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)},
            globalSecret)  # TODO hide pwd

        return jsonify({'token': token.decode('UTF-8'), 'user': user})
