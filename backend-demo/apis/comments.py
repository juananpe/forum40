from flask_restplus import Resource
from db import mongo
from apis import api

ns = api.namespace('comments', description="comments api")

@ns.route('/')
class CommentsGet(Resource):
    def get(self):
        return {'hello': 'comments'}, 200

@ns.route('/count')
class CommentsCount(Resource):
    def get(self):
        coll = mongo.db.Comments
        return {'count': coll.find().count()}, 200
