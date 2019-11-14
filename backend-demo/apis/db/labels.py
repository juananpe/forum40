from flask import request, Response
from flask_restplus import Resource, reqparse

from apis.db import api
from db import postgres_con
from db.queries import *

from bson import json_util
import json

from jwt_auth.token import token_required

ns = api.namespace('labels', description="labels api")

@ns.route('/<int:source_id>')
class LabelsGetAll(Resource):
    def get(self, source_id):
        postgres = postgres_con.cursor()
        postgres.execute(SELECT_NAMES_FROM_LABES(source_id))
        d_list = [t[0] for t in postgres.fetchall()]

        postgres.execute(SELECT_IDS_FROM_LABES(source_id))
        i_list = [t[0] for t in postgres.fetchall()]

        return { 
            "labels" : d_list,
            "ids" : i_list
        }

@ns.route('/count')
class LabelsCount(Resource):
    def get(self):
        postgres = postgres_con.cursor()
        postgres.execute(COUNT_LABELS)
        db_return = postgres.fetchone()

        if db_return:
             return {'count': db_return[0]}, 200
        
        return {"msg": "Error"}, 400        

@ns.route('/id/<string:name>')
class LabelsId(Resource):
    def get(self, name):
        postgres = postgres_con.cursor()
        postgres.execute(SELECT_ID_FROM_LABELS_BY_NAME(name))
        db_return = postgres.fetchone()
        if db_return:
            return {'id': db_return[0]}, 200
        else:
            return {"msg": f"Label: '{name}' does not exists!"}, 400 


@ns.route('/binary/<string:label_name>/<int:source_id>')
class AddLabel(Resource):
    @token_required
    @api.doc(security='apikey')
    def put(self, data, label_name, source_id):
        postgres = postgres_con.cursor()
        postgres.execute(COUNT_LABELS_BY_NAME(label_name))
        db_result = postgres.fetchone()

        if db_result:
            if db_result[0] >= 1:
                return { 'msg' : 'Label already exists.' } , 400

        postgres.execute(SELECT_MAX_LABEL('labels'))
        max_id = postgres.fetchone()[0]

        postgres.execute(INSERT_LABEL(max_id+1, 'classification', label_name, source_id))
        postgres_con.commit()
        
        return "ok", 200 
                
