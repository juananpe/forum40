from flask import request
from flask_restplus import Resource, reqparse

from apis.db import api

from db import postgres

ns = api.namespace('users', description="users api")

@ns.route('/count')
class UsersCount(Resource):
    def get(self):
        postgres.execute("SELECT COUNT(*) FROM users;")
        db_return = postgres.fetchone()

        if db_return:
             return {'count': db_return[0]}, 200
        
        return {"msg": "Error"}, 400