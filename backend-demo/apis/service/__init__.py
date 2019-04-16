from flask import Blueprint
from flask_restplus import Api

blueprint = Blueprint('service_api', __name__, )

api = Api(version='1.0', title='Service-API', description="An API for usercomments")
api.init_app(blueprint)


from apis.service.meta_comment import ns as meta_comment_namespace

# add namespaces
api.add_namespace(meta_comment_namespace)
