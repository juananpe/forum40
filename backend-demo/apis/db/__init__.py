from flask import Blueprint
from flask_restplus import Api

from jwt_auth import authorization

blueprint = Blueprint('db_api', __name__)

api = Api(authorizations=authorization, version='1.0', title='User-Comments-API', description="An API for usercomments")
api.init_app(blueprint)

from apis.db.auth import ns as auth_namespace
from apis.db.comments import ns as comments_namespace
from apis.db.labels import ns as labels_namespace
from apis.db.annotations import ns as annotations_namespace
from apis.db.documents import ns as documents_namespace
from apis.db.sources import ns as sources_namespace
from apis.db.users import ns as users_namespace
from apis.db.models import ns as models_namespace


# add namespaces
api.add_namespace(auth_namespace)
api.add_namespace(comments_namespace)
api.add_namespace(labels_namespace)
api.add_namespace(annotations_namespace)
api.add_namespace(documents_namespace)
api.add_namespace(sources_namespace)
api.add_namespace(users_namespace)
api.add_namespace(models_namespace)