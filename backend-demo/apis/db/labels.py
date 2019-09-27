from flask import request, Response
from flask_restplus import Resource, reqparse

from apis.db import api
from db import postgres
from db import postgres_con

from db import mongo

from bson import json_util
import json

from jwt_auth.token import token_required

ns = api.namespace('labels', description="labels api")

@ns.route('/')
class LabelsGetAll(Resource):
    def get(self):
        postgres.execute('SELECT name FROM labels')
        d_list = [t[0] for t in postgres.fetchall()]

        postgres.execute('SELECT id FROM labels')
        i_list = [t[0] for t in postgres.fetchall()]

        return { 
            "labels" : d_list,
            "ids" : i_list
        }

@ns.route('/count')
class LabelsCount(Resource):
    def get(self):
        postgres.execute("SELECT COUNT(*) FROM labels;")
        db_return = postgres.fetchone()

        if db_return:
             return {'count': db_return[0]}, 200
        
        return {"msg": "Error"}, 400        

@ns.route('/id/<string:name>')
class LabelsId(Resource):
    def get(self, name):
        postgres.execute("SELECT id FROM labels WHERE name = '{0}';".format(name))
        db_return = postgres.fetchone()
        if db_return:
            return {'id': db_return[0]}, 200
        else:
            return {"msg": "Label: '{0}' does not exists!"}, 400


@ns.route('/binary/<string:label_name>')
class AddLabel(Resource):
    @token_required
    @api.doc(security='apikey')
    def put(self, data, label_name):

        postgres.execute("SELECT COUNT(*) FROM labels WHERE name = '{0}';".format(label_name))
        db_result = postgres.fetchone()

        if db_result:
            if db_result[0] >= 1:
                return { 'msg' : 'Label already exists.' } , 400

        postgres.execute('SELECT MAX(id) FROM labels')
        max_id = postgres.fetchone()[0]

        postgres.execute(
            "INSERT INTO labels (id, type, name) VALUES(%s, %s, %s)", 
            (max_id+1 , 'classification', label_name))
        postgres_con.commit()
        
        return "ok", 200 
                
