#!/usr/bin/env python3.6
from flask import Flask, request
from flask_cors import CORS

import settings

from db import mongo
from core.proxy_wrapper import ReverseProxied
from core.encoder import JSONMongoEncoder

from apis.db import blueprint as db_blueprint
from apis.service import blueprint as service_blueprint

app = Flask(__name__)

# configure app
app.config['MONGO_DBNAME'] = settings.MONGO_DBNAME
app.config['MONGO_URI'] = settings.MONGO_URI
app.config['RESTPLUS_MASK_SWAGGER'] = settings.RESTPLUS_MASK_SWAGGER
app.config['RESTPLUS_VALIDATE'] = settings.RESTPLUS_VALIDATE
app.config['SWAGGER_UI_DOC_EXPANSION'] = settings.SWAGGER_UI_DOC_EXPANSION
app.config['JWT_SECRET_KEY'] = settings.JWT_SECRET_KEY

# main page
@app.route("/")
def hello():
    url = str(request.url_rule)
    return '<a href="{0}api/db/">User-Comments-API</a> </br> <a href="{0}api/service/">Service-API</a> </br> <a href="{0}api/meta/">Meta-Comment-API</a> </br> <a href="{0}api/offlang">Offensive-Language-API</a> </br>'.format(url)

# add blueprints
app.register_blueprint(db_blueprint, url_prefix='/db')
app.register_blueprint(service_blueprint, url_prefix='/service')

# add extensions
app.wsgi_app = ReverseProxied(app.wsgi_app)
CORS(app)
mongo.init_app(app)
app.json_encoder = JSONMongoEncoder

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)
