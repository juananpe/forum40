from flask import Flask
from logging.config import dictConfig
from flask_restplus import Api, Resource, fields
from core.proxy_wrapper import ReverseProxied

from utils import concat

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
class ClassifierService(Resource):
    @api.expect(comments_model)
    def post(self):
        comments = api.payload.get('comments', [])
        comment_texts = [
            concat(c.get('title', ''), c.get('text', ''))for c in comments
        ]


        # do stuff here ...
        results = [{'tmp':comment_texts}]

        return results, 200


# run app manually
if __name__ == "__main__":
    app.run(threaded = True)
