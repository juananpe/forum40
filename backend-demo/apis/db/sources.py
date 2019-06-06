from flask import request
from flask_restplus import Resource, reqparse, fields
from apis.db import api
from models.db_models import aggregate_model

from db import mongo
from db.mongo_util import aggregate

ns = api.namespace('sources', description="sources api")

@ns.route('/count')
class SourcesCount(Resource):
    def get(self):
        coll = mongo.db.Sources
        return {'count': coll.find().count()}, 200
