from flask import Blueprint
from flask_restplus import Api

from jwt_auth import authorization

blueprint = Blueprint('deaft1_api', __name__)

api = Api(authorizations=authorization, version='1.0', title='Draft1-API', description="An API for ...")
api.init_app(blueprint)

from apis.draft1.namespace1 import ns as draft1_namespace

# add namespaces
api.add_namespace(draft1_namespace)
