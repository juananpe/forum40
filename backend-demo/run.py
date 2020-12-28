#!/usr/bin/env python3.6
from flask import Flask, request
from flask_cors import CORS

from apis.classification import blueprint as classification_blueprint
from apis.db import blueprint as db_blueprint
from apis.embeddings import blueprint as embeddings_blueprint
from config import settings
from core.proxy_wrapper import ReverseProxied

app = Flask(__name__)

# configure app
app.config['RESTPLUS_MASK_SWAGGER'] = settings.RESTPLUS_MASK_SWAGGER
app.config['RESTPLUS_VALIDATE'] = settings.RESTPLUS_VALIDATE
app.config['SWAGGER_UI_DOC_EXPANSION'] = settings.SWAGGER_UI_DOC_EXPANSION
app.config['JWT_SECRET_KEY'] = settings.JWT_SECRET_KEY


# main page
@app.route("/")
def hello():
    base_url = str(request.url_rule)
    entries = [
        ('api/db/', 'User-Comments-API'),
        ('api/classification', 'Classification-API'),
        ('api/similarity', 'Similarity-API'),
        ('api/embedding', 'Embedding-API'),
    ]

    return '\n'.join(f'<a href="{base_url}{path}">{name}</a> </br>' for path, name in entries)


# add blueprints
app.register_blueprint(db_blueprint, url_prefix='/db')
app.register_blueprint(embeddings_blueprint, url_prefix='/similarity')
app.register_blueprint(classification_blueprint, url_prefix='/classification')

# add extensions
app.wsgi_app = ReverseProxied(app.wsgi_app)
CORS(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)
