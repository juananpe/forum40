from flask import request, Response
from flask_restplus import Resource, reqparse

from apis.db import api
from db import mongo

from bson import json_util
import json

from jwt_auth.token import token_required

ns = api.namespace('labels', description="labels api")

@ns.route('/')
class LabelsGetAll(Resource):
    def get(self):
        coll = mongo.db.Labels
        labels = coll.find({}, {"description" : 1, "_id": 1})
        i_list = []
        d_list = []
        for l in labels:
            i_list.append(str(l["_id"]))
            d_list.append(l["description"])
        return { 
            "labels" : d_list,
            "ids" : i_list
        }

@ns.route('/count')
class LabelsCount(Resource):
    def get(self):
        coll = mongo.db.Labels
        return {'count': coll.find().count()}, 200

@ns.route('/id/<string:name>')
class LabelsId(Resource):
    def get(self, name):
        coll = mongo.db.Labels
        c = coll.find_one({"description" : name}, {"_id": 1})
        id = None
        if c: 
            id = str(c["_id"])
        return {"id" : id }, 200

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
                
