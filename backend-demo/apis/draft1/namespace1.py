from flask_restplus import Resource

from apis.db import api

ns = api.namespace('draft1', description="draft1 api")

@ns.route('/test')
class TestRoute(Resource):
    def get(self):
        return {'Hello': 'Test'}