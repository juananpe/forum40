from flask import Flask
from logging.config import dictConfig
from flask_restplus import Api, Resource, fields
from core.proxy_wrapper import ReverseProxied

import fastText
import keras
from forum import concat, classify

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

OFFLANG_CLASSES = ['other', 'offensive']

# define app
app = Flask(__name__)
app.wsgi_app = ReverseProxied(app.wsgi_app)

# load fasttext model
app.logger.debug('Loading fasttext model')
ft = fastText.load_model("model/wiki.de.bin")
app.logger.debug('Fasttext model loaded')

# Load keras model
app.logger.debug('Loading keras model')
model: keras.Model = keras.models.load_model("model/classification_model_tl_twitterclasses7m_1000_suf_bu.h5")
model._make_predict_function()
app.logger.debug('Keras model loaded')

# define API
api = Api(app, version='0.1', title='Offensive-Language-Classification-API',
          description="An API for classifying user comments")

comment_model = api.model(
    'comment', {
        'title': fields.String('Title of the comment.'),
        'text': fields.String('Text of the comment.')})

comments_model = api.model('comments', {
    'comments': fields.List(fields.Nested(comment_model))
})




@api.route('/comments')
class OfflangCommentsClassifier(Resource):
    @api.expect(comments_model)
    def post(self):
        comments = api.payload.get('comments', [])
        comment_texts = [
            concat(c.get('title', ''), c.get('text', ''))for c in comments
        ]
        results = classify(model, ft, comment_texts, OFFLANG_CLASSES)
        # results = [{'tmp':comment_texts}]
        return results, 200


# run app manually
if __name__ == "__main__":
    app.run(threaded = True)
