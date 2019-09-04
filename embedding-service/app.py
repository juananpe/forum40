from flask import Flask
from logging.config import dictConfig
from flask_restplus import Api, Resource, fields
from core.proxy_wrapper import ReverseProxied
import nmslib, pickle
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
retriever = RetrieveComment('mongo', 27017)

# define API
api = Api(app, version='0.1', title='Embedding API',
          description="An API for embedding user comments")

# API for comment texts
comment_model = api.model(
    'comment', {
        'text': fields.String('Text of the comment.')
    })
comments_model = api.model('comments', {
    'comments': fields.List(fields.Nested(comment_model))
})

# API for comment ids
commentid_model = api.model(
    'comment_id', {
        'id': fields.String('Mongodb object ID')
    })
commentsid_model = api.model('comments_id', {
    'ids': fields.List(fields.Nested(commentid_model))
})


@api.route('/comment')
class CommentsEmbedding(Resource):
    @api.expect(comments_model)
    def post(self):
        comments = api.payload.get('comments', [])
        comment_texts = [
            concat(c.get('title', ''), c.get('text', '')) for c in comments
        ]
        results = be.extract_features(comment_texts)
        return results, 200


 
       


"""edited part"""
#load_indexes
get_comment=RetrieveComment()

commentid_model = api.model(
    'comment_id', {
        'id': fields.String('5cadf570694377c8a2f450d8')})
        
commentsid_model = api.model('comments_id', {
    'ids': fields.List(fields.Nested(commentid_model))
})



@api.route('/commentid')
class Idembeddings(Resource):
    @api.expect(commentsid_model)
    def post(self):
        comments_id = api.payload.get('ids', [])
        all_ids= [c.get('id', '') for c in comments_id]
        results = []
        for _id in all_ids:
            embedding=get_comment.get_embeddings(_id)
            results.append(embedding)
        return results, 200


@api.route('/similarids')
class similarIds(Resource):
    @api.expect(commentsid_model)
    def post(self):
        comments_id = api.payload.get('ids', [])
        all_ids= [c.get('id', '') for c in comments_id]
        results =[]
        for _id in all_ids:
            ids=get_comment.get_nearest_ids(_id)
            results.append(ids)
        return results, 200


        comment_texts = [c.get('text', '') for c in comments]
        results = be.extract_features(comment_texts)
        return results, 200

@api.route('/embedding')
class IdEmbedding(Resource):
    @api.expect(commentsid_model)
    def post(self):
        comments_id = api.payload.get('ids', [])
        all_ids = [c.get('id', '') for c in comments_id]
        results = []
        for _id in all_ids:
            embedding = retriever.get_embeddings(_id)
            results.append(embedding)
        return results, 200


@api.route('/similar-ids')
class SimilarIds(Resource):
    @api.expect(commentsid_model)
    def post(self):
        comments_id = api.payload.get('ids', [])
        all_ids= [c.get('id', '') for c in comments_id]
        results =[]
        for _id in all_ids:
            ids = retriever.get_nearest_ids(_id)
            results.append(ids)
        return results, 200

@api.route('/similar-comments')
class SimilarIds(Resource):
    @api.expect(comments_model)
    def post(self):
        comments = api.payload.get('comments', [])
        comment_texts = [c.get('text', '') for c in comments]
        embeddings = be.extract_features(comment_texts)
        results = []
        for embedding in embeddings:
            nn_ids = retriever.get_nearest_embeddings(embedding)
            results.append([retriever.get_comment_text(id) for id in nn_ids])
        return results, 200

# todo api
# [.] get embedding given comment id
# [X] get embedding given text
# [.] get nearest neighbors given comment id
# [.] get nearest neighbors given text

# run app manually
if __name__ == "__main__":
    app.run(threaded = True)
