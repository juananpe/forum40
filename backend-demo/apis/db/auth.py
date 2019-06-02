from flask import jsonify, make_response
from flask_restplus import Resource

from apis.db import api
from db import mongo

import json
import datetime
from bson import ObjectId


from jwt_auth.token import token_required

import jwt
from werkzeug.security import generate_password_hash, check_password_hash

ns = api.namespace('auth', description="auth api")

@ns.route('/test')
class AuthTest(Resource):
    @token_required
    @api.doc(security='apikey')
    def get(self, data):
        user = self["user"]

        return {"ok": user }, 200

@ns.route('/login/<string:username>/<string:password>')
class AuthLogin(Resource):
    def get(self, username, password):

        users_coll = mongo.cx["admin"].Users
        user_mongo = users_coll.find_one({"user" : username})
        login_log_coll = mongo.cx["admin"].LoginLog
        tokens_coll = mongo.cx["admin"].Tokens
        secrets_coll = mongo.cx["admin"].Secrets

        if user_mongo and not user_mongo.get('blocked') and user_mongo.get('password') == password: # TODO sec check
            secret_mongo = secrets_coll.find_one().get('globalSecret')
            token = jwt.encode({
                'user' : username, 
                'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, 
                secret_mongo) # TODO hide pwd

            login_log_coll.insert({ "user": username, "timeStamp" : datetime.datetime.now(), "success": True })
            tokens_coll.update({ "user": username}, { "user": username, "token": token}, upsert=True)

            return jsonify({'token' : token.decode('UTF-8'), 'user' : username})
        
        login_log_coll.insert({ "user": username, "timeStamp" : datetime.datetime.now(), "success": False })
        return make_response('Could not verify!', 401)

@ns.route('/logout/')
class AuthLogout(Resource):
    @token_required
    @api.doc(security='apikey')
    def get(self, data):
        
        user = self["user"]

        tokens_coll = mongo.cx["admin"].Tokens
        tokens_coll.update({ "user": user}, { "user": user, "token": None})
        return {"logout": "ok"}, 200

@ns.route('/refreshToken/')
class AuthRefresh(Resource):
    @token_required
    @api.doc(security='apikey')
    def get(self, data):

        user = self["user"]

        tokens_coll = mongo.cx["admin"].Tokens
        secrets_coll = mongo.cx["admin"].Secrets
        secret_mongo = secrets_coll.find_one().get('globalSecret')

        token = jwt.encode({
            'user' : user, 
            'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=60)}, 
            secret_mongo) # TODO hide pwd

        tokens_coll.update({ "user": user}, { "user": user, "token": token})

        return jsonify({'token' : token.decode('UTF-8'), 'user' : user})



@ns.route('/initDB/')
class AuthInitDB(Resource):
    def get(self):
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
        