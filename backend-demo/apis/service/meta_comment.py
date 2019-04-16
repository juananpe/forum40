from flask import request
from flask_restplus import Resource, reqparse

from apis.service import api

from db import mongo

ns = api.namespace('meta_comment', description="meta comment api")

@ns.route('/')
class CommentsGet(Resource):
    def get(self):
        return {'hello': 'service'}, 200
