from flask import request
from flask_restplus import Resource, reqparse

from apis.db import api
from models.db_models import aggregate_model

from db import mongo
from db.mongo_util import aggregate

from bson import json_util

ns = api.namespace('labels', description="labels api")

@ns.route('/')
class LabelsGetAll(Resource):
    def get(self):
        coll = mongo.db.Labels
        descriptions = coll.find({}, {"description" : 1, "_id": 0})
        d_list = [d["description"] for d in  descriptions]
        return {'labels': d_list}, 200

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
