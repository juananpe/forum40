from flask import Flask
from logging.config import dictConfig
from flask_restplus import Api, Resource, fields
from core.proxy_wrapper import ReverseProxied
from retrieve_comments import RetrieveComment
from tasks import get_embeddings

import os, logging

from utils.tasks import SingleProcessManager

# pg config
pg_host = os.getenv('PG_HOST', 'postgres')
pg_port = os.getenv('PG_PORT', '5432')

process_manager = SingleProcessManager(pg_host, pg_port)

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

# db connection
try:
    retriever = RetrieveComment(pg_host, pg_port)
except:
    app.logger.error('DB connection failed.')
    exit(1)

# define API
api = Api(app, version='0.1', title='Embedding API',
          description="An API for embedding user comments")

# API for comments
comments_model = api.model('Comments', {
    'comments': fields.List(
        fields.String,
        example=[
            'Ich bin darüber hocherfreut. Weiter so!',
            'Nie wieder! Das was absolut schrecklich.'
        ],
        required=True
    ),
})
sim_comments_model = api.model('SimComments', {
    'comments': fields.List(
        fields.String,
        example=[
            'Ich bin darüber hocherfreut. Weiter so!',
            'Nie wieder! Das was absolut schrecklich.'
        ],
        required=True
    ),
    'n': fields.Integer(
        description="Number of similar comments to retrieve",
        required=False,
        example=10
    )
})

# API for comment ids
id_model = api.model('Id', {
    'ids': fields.List(
        fields.Integer,
        required=True,
        example=[200]
    )
})
sim_id_model = api.model('SimId', {
    'ids': fields.List(
        fields.Integer,
        required=True,
        example=[200]
    ),
    'n': fields.Integer(
        description="Number of similar comments to retrieve",
        required=False,
        example=10
    )
})

# API for task ids
tasks_model = api.model('TaskId', {
    'task_id': fields.String
})


@api.route('/comment')
class CommentsEmbedding(Resource):
    @api.expect(comments_model)
    def post(self):
        comment_texts = api.payload.get('comments', [])
        results = get_embeddings(comment_texts)
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
        results = []
        for _id in comments_ids:
            ids = retriever.get_nearest_for_id(_id, n=n)
            results.append(ids)
        return results, 200


@api.route('/similar-comments')
class SimilarComments(Resource):
    @api.expect(sim_comments_model)
    def post(self):
        comment_texts = api.payload.get('comments', [])
        n = api.payload.get('n', 10)

        # get embedding
        embeddings = get_embeddings(comment_texts)
        results = []
        for embedding in embeddings:
            nn_ids = retriever.get_nearest_for_embedding(embedding)
            results.append([retriever.get_comment_text(id) for id in nn_ids])
        return results, 200


@api.route('/tasks')
class Tasks(Resource):
    def get(self):
        results = process_manager.tasks()
        return results, 200


@api.route('/tasks/<taskname>')
class TaskStatus(Resource):
    def get(self, taskname):
        results = process_manager.status(taskname)
        return results, 200


@api.route('/tasks/<taskname>/invoke')
class TaskInvoke(Resource):
    def get(self, taskname):
        results = process_manager.invoke(taskname)
        return results, 200


@api.route('/tasks/<taskname>/abort')
class TaskAbort(Resource):
    def get(self, taskname):
        results = process_manager.abort(taskname)
        return results, 200

@api.route('/tasks/clear')
class Tasks(Resource):
    def get(self):
        results = process_manager.clear()
        return results, 200


# run app manually
if __name__ == "__main__":
    app.run(threaded=True)
