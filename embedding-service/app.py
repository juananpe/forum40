from flask import Flask
from logging.config import dictConfig
from flask_restplus import Api, Resource, fields
from core.proxy_wrapper import ReverseProxied
from BertFeatureExtractor import BertFeatureExtractor
from utils import concat
from retrieve_comments import RetrieveComment


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

#load BERT model
app.logger.debug('Loading BERT model')
be = BertFeatureExtractor()
app.logger.debug('BERT model loaded')

# db connection
try:
    retriever = RetrieveComment('postgres', 5432)
except:
    app.logger.error('DB connection failed.')

# define API
api = Api(app, version='0.1', title='Embedding API',
          description="An API for embedding user comments")

# API for comments
comments_model = api.model('Comments', {
    'comments': fields.List(fields.String)
})
sim_comments_model = api.model('SimComments', {
    'comments': fields.List(fields.String),
    'n' : fields.Integer
})

# API for comment ids
id_model = api.model('Id', {
    'ids': fields.List(fields.Integer)
})
sim_id_model = api.model('SimId', {
    'ids': fields.List(fields.Integer),
    'n' : fields.Integer
})

@api.route('/comment')
class CommentsEmbedding(Resource):
    @api.expect(comments_model)
    def post(self):
        comment_texts = api.payload.get('comments', [])
        results = be.extract_features(comment_texts)
        return results, 200


@api.route('/id')
class IdEmbedding(Resource):
    @api.expect(id_model)
    def post(self):
        comments_id = api.payload.get('ids', [])
        all_ids = [int(c) for c in comments_id]
        results = []
        for id in all_ids:
            embedding = retriever.get_embedding(id)
            results.append(embedding)
        return results, 200


@api.route('/similar-ids')
class SimilarIds(Resource):
    @api.expect(sim_id_model)
    def post(self):
        comments_ids = api.payload.get('ids', [])
        n = api.payload.get('n', 10)
        if n == 0:
            n = 1
        results =[]
        for _id in comments_ids:
            ids = retriever.get_nearest_for_id(_id, n = n)
            results.append(ids)
        return results, 200


@api.route('/similar-comments')
class SimilarComments(Resource):
    @api.expect(sim_comments_model)
    def post(self):
        comment_texts = api.payload.get('comments', [])
        n = api.payload.get('n', 10)

        # get embedding
        embeddings = be.extract_features(comment_texts)
        results = []
        for embedding in embeddings:
            nn_ids = retriever.get_nearest_for_embedding(embedding)
            results.append([retriever.get_comment_text(id) for id in nn_ids])
        return results, 200


# run app manually
if __name__ == "__main__":
    app.run(threaded = True)
