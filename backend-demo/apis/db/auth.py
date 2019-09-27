from flask import jsonify, make_response
from flask_restplus import Resource

from apis.db import api
from db import mongo
from db import postgres

import json
import datetime
from bson import ObjectId


from jwt_auth.token import token_required

import jwt
from werkzeug.security import generate_password_hash, check_password_hash

ns = api.namespace('auth', description="auth api")

globalSecret = "eh9Df9G27gahgHJ7g2oGQz6Ug5he6ud5shd" # TODO hide

@ns.route('/test')
class AuthTest(Resource):
    @token_required
    @api.doc(security='apikey')
    def get(self, data):
        user = self["user"]

        return {"ok": user }, 200
import sys

@ns.route('/login/<string:username>/<string:password>')
class AuthLogin(Resource):
    def get(self, username, password):

        postgres.execute("SELECT password FROM users WHERE name = '{0}';".format(username))
        db_result = postgres.fetchone()

        if not db_result or db_result[0] != password or password == None:
            return make_response('Could not verify!', 401)
        else :
            token = jwt.encode({
                'user' : username, 
                'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=60)}, 
                globalSecret
            )
            return jsonify({'token' : token.decode('UTF-8'), 'user' : username})

@ns.route('/logout/')
class AuthLogout(Resource):
    @token_required
    @api.doc(security='apikey')
    @api.deprecated
    def get(self, data):
        return {"Warning": "logout not used"}, 200

@ns.route('/refreshToken/')
class AuthRefresh(Resource):
    @token_required
    @api.doc(security='apikey')
    def get(self, data):
        user = self["user"]

        token = jwt.encode({
            'user' : user, 
            'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=60)}, 
            globalSecret) # TODO hide pwd

        return jsonify({'token' : token.decode('UTF-8'), 'user' : user})



@ns.route('/initDB/')
class AuthInitDB(Resource):
    def put(self):

        db = mongo.cx["admin"]
        if not "Users" in  db.collection_names():
            users_coll = db.Users
            secrets_coll = db.Secrets

            users_coll.insert_many([{ 
                "user" : "user1", 
                "password" : "22880", 
                "blocked" : False
            },
            { 
                "user" : "user2", 
                "password" : "0815", 
                "blocked" : False
            },
            { 
                "user" : "Hugo", 
                "password" : "123", 
                "blocked" : True
            }])

            secrets_coll.insert({
                "globalSecret" : "eh9Df9G27gahgHJ7g2oGQz6Ug5he6ud5shd"
            })

            return {"msg": "Database setup completed"}

        return {"msg": "Database already exists."}
        