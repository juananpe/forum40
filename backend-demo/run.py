#!/usr/bin/env python3.6
from flask import Flask, request
from flask_cors import CORS

from config import settings

from core.proxy_wrapper import ReverseProxied

from apis.db import blueprint as db_blueprint
from apis.service import blueprint as service_blueprint
from apis.embeddings import blueprint as embeddings_blueprint
from apis.classification import blueprint as classification_blueprint

app = Flask(__name__)

# configure app
app.config['RESTPLUS_MASK_SWAGGER'] = settings.RESTPLUS_MASK_SWAGGER
app.config['RESTPLUS_VALIDATE'] = settings.RESTPLUS_VALIDATE
app.config['SWAGGER_UI_DOC_EXPANSION'] = settings.SWAGGER_UI_DOC_EXPANSION
app.config['JWT_SECRET_KEY'] = settings.JWT_SECRET_KEY

# main page
@app.route("/")
def hello():
    url = str(request.url_rule)
    return '<a href="{0}api/db/">User-Comments-API</a> </br> ' \
           '<a href="{0}api/service/">Service-API</a> </br> ' \
           '<a href="{0}api/meta/">Meta-Comment-API</a> </br> ' \
           '<a href="{0}api/classification">Classification-API</a> </br>' \
           '<a href="{0}api/similarity">Similarity-API</a> </br>' \
           '<a href="{0}api/embedding">Embedding-API</a> </br>'.format(url)

# add blueprints
app.register_blueprint(db_blueprint, url_prefix='/db')
app.register_blueprint(service_blueprint, url_prefix='/service')
app.register_blueprint(embeddings_blueprint, url_prefix='/similarity')
app.register_blueprint(classification_blueprint, url_prefix='/classification')

# add extensions
app.wsgi_app = ReverseProxied(app.wsgi_app)
CORS(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)
