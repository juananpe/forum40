from flask import request, Response
from flask_restplus import Resource, reqparse

from apis.db import api
from db import postgres
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
        coll = mongo.db.Labels
        c = coll.find_one({"description" : label_name})
        if c: 
            return 'Label already exists.', 400

        coll.insert({  
            "type" : "binary", 
            "description" : label_name, 
            "scale" : "ordinal",
            "annotatorId": self["user"],
        })

        return "ok", 200
                
