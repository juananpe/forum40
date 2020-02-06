from flask_restplus import Resource

from apis.embeddings import api
# from config import settings

ns = api.namespace('embeddings', description="Embeddings-API namespace")

@ns.route('/test')
class TestRoute(Resource):
    def get(self):
        return {'embedding service url': 'test'}