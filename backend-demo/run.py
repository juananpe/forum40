#!/usr/bin/env python3.6
from flask import Flask, Blueprint
from flask_cors import CORS
from flask_restplus import Api

import settings
from db import mongo
from apis import api
from core.proxy_wrapper import ReverseProxied

from apis.comments import ns as comments_namespace
from apis.documents import ns as documents_namespace
from apis.labels import ns as labels_namespace
from apis.sources import ns as sources_namespace
from apis.users import ns as users_namespace

app = Flask(__name__)

# configure app
app.config['MONGO_DBNAME'] = settings.MONGO_DBNAME
app.config['MONGO_URI'] = settings.MONGO_URI
app.config['RESTPLUS_MASK_SWAGGER'] = settings.RESTPLUS_MASK_SWAGGER
app.config['RESTPLUS_VALIDATE'] = settings.RESTPLUS_VALIDATE
app.config['SWAGGER_UI_DOC_EXPANSION'] = settings.SWAGGER_UI_DOC_EXPANSION

# add blueprint
blueprint = Blueprint('api', __name__)
api.init_app(blueprint)
app.register_blueprint(blueprint)

# add namespaces
api.add_namespace(comments_namespace)
api.add_namespace(documents_namespace)
api.add_namespace(labels_namespace)
api.add_namespace(sources_namespace)
api.add_namespace(users_namespace)

# add extensions
app.wsgi_app = ReverseProxied(app.wsgi_app)
CORS(app)
mongo.init_app(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)
