from flask import Blueprint
from flask_restplus import Api

from jwt_auth import authorization
from apis.embeddings.tasks import ns as embeddings_namespace

blueprint = Blueprint('embedding_api', __name__)

# authorizations=authorization

api = Api(version='1.0', title='Embedding-API', description="Access pre-computed embeddings and comments based on embedding similarity")
api.init_app(blueprint)


# add namespaces
api.add_namespace(embeddings_namespace)
