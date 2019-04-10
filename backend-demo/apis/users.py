from flask_restplus import Resource
from db import mongo
from apis import api

ns = api.namespace('users', description="users api")

@ns.route('/')
class UsersGet(Resource):
    def get(self):
        return {'hello': 'users'}, 200

@ns.route('/count')
class UsersCount(Resource):
    def get(self):
        coll = mongo.db.Users
        return {'count': coll.find().count()}, 200
