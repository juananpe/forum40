from flask import Flask
from logging.config import dictConfig
from flask_restplus import Api, Resource, fields
from core.proxy_wrapper import ReverseProxied
from tasks import get_embeddings

import logging

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi']
    }
})

# define app
app = Flask(__name__)
app.wsgi_app = ReverseProxied(app.wsgi_app)
app.logger.setLevel(logging.INFO)


# define API
api = Api(app, version='1.0', title='Embedding API',
          description="An API for embedding strings")

# API for strings
strings_model = api.model('Texts', {
    'texts': fields.List(
        fields.String,
        example=[
            'Ich bin darüber hocherfreut. Weiter so!',
            'Nie wieder! Das was absolut schrecklich.'
        ],
        required=True
    ),
})


@api.route('/embed')
class StringsEmbedding(Resource):
    @api.expect(strings_model)
    def post(self):
        comment_texts = api.payload.get('texts', [])
        results = get_embeddings(comment_texts)
        return results, 200


# run app manually
if __name__ == "__main__":
    app.run(threaded=True, port=5060)
