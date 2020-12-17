import datetime
from flask.blueprints import BlueprintSetupState
from typing import Any

import json
from flask import Blueprint
from flask_restplus import Api

from apis.db.annotations import ns as annotations_namespace
from apis.db.auth import ns as auth_namespace
from apis.db.comments import ns as comments_namespace
from apis.db.documents import ns as documents_namespace
from apis.db.labels import ns as labels_namespace
from apis.db.models import ns as models_namespace
from apis.db.sources import ns as sources_namespace
from jwt_auth import authorization


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        else:
            return super().default(o)


blueprint = Blueprint('db_api', __name__)


@blueprint.record
def record_json_encoder(setup_state: BlueprintSetupState):
    setup_state.app.config['RESTPLUS_JSON'] = {'cls': CustomJSONEncoder}


api = Api(authorizations=authorization, version='1.0', title='User-Comments-API', description="An API for usercomments")
api.init_app(blueprint)

# add namespaces
api.add_namespace(auth_namespace)
api.add_namespace(comments_namespace)
api.add_namespace(labels_namespace)
api.add_namespace(annotations_namespace)
api.add_namespace(documents_namespace)
api.add_namespace(sources_namespace)
api.add_namespace(models_namespace)
