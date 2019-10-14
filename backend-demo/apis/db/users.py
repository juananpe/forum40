from flask import request
from flask_restplus import Resource, reqparse

from apis.db import api

from db import postgres_con
from db.queries import COUNT_USERS

ns = api.namespace('users', description="users api")

@ns.route('/count')
class UsersCount(Resource):
    def get(self):
        postgres = postgres_con.cursor()
        postgres.execute(COUNT_USERS)
        db_return = postgres.fetchone()

        if db_return:
             return {'count': db_return[0]}, 200
        
        return {"msg": "Error"}, 400