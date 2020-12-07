from flask import Blueprint
from flask_restplus import Api

from apis.classification.tasks import ns as classification_namespace

blueprint = Blueprint('classification_api', __name__)

api = Api(version='1.0', title='Classification-API', description="Classify comments based on pre-computed embeddings")
api.init_app(blueprint)

# add namespaces
api.add_namespace(classification_namespace)
