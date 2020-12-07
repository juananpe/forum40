from flask import Blueprint
from flask_restplus import Api

from jwt_auth import authorization

from apis.classification.tasks import ns as classification_namespace

blueprint = Blueprint('classification_api', __name__)

# authorizations=authorization

api = Api(version='1.0', title='Classification-API', description="Classify comments based on pre-computed embeddings")
api.init_app(blueprint)

# add namespaces
api.add_namespace(classification_namespace)
