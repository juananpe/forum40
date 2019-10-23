from flask import Flask
from logging.config import dictConfig
from flask_restplus import Api, Resource, fields
from core.proxy_wrapper import ReverseProxied
from retrieve_comments import RetrieveComment
from tasks import celery_app, index_comments, embed_comments, get_embeddings

import os, logging

# pg config
pg_host = os.getenv('PG_HOST', 'postgres')
pg_port = os.getenv('PG_PORT', 5432)

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

# define API
api = Api(app, version='0.1', title='Embedding API',
          description="An API for embedding user comments")

# API for comments
comments_model = api.model('Comments', {
    'comments': fields.List(fields.String)
})
sim_comments_model = api.model('SimComments', {
    'comments': fields.List(fields.String),
    'n' : fields.Integer(
        description = "Number of similar comments to retrieve",
        required = False,
        example = 10
    )
})

# API for comment ids
id_model = api.model('Id', {
    'ids': fields.List(fields.Integer)
})
sim_id_model = api.model('SimId', {
    'ids': fields.List(fields.Integer),
    'n' : fields.Integer(
        description = "Number of similar comments to retrieve",
        required = False,
        example = 10
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
        embeddings = get_embeddings(comment_texts)
        results = []
        for embedding in embeddings:
            nn_ids = retriever.get_nearest_for_embedding(embedding)
            results.append([retriever.get_comment_text(id) for id in nn_ids])
        return results, 200


@api.route('/tasks/indexing')
class IndexComments(Resource):
    def get(self):

        i = celery_app.control.inspect()
        running_tasks = i.active()

        # import pdb
        # pdb.set_trace()

        app.logger.debug(running_tasks)

        # check if indexing is already running
        if running_tasks:
            first_worker_id = [k for k in running_tasks.keys()][0]
            first_worker_tasks = running_tasks[first_worker_id]
            if first_worker_tasks:
                for first_worker_task in first_worker_tasks:
                    if first_worker_task['name'].endswith('index_comments'):
                        results = {
                            "message" : "Indexing is already running",
                            "details" : first_worker_task
                        }
                        return results, 200

        # start indexing
        t = index_comments.delay(pg_host, pg_port)
        results = {
            "message" : "Indexing started.",
            "task.id" : t.id
        }

        app.logger.debug(i.active())

        return results, 200

@api.route('/tasks/embedding')
class EmbedComments(Resource):
    def get(self):

        i = celery_app.control.inspect()
        running_tasks = i.active()

        # check if indexing is already running
        if running_tasks:
            first_worker_id = [k for k in running_tasks.keys()][0]
            first_worker_tasks = running_tasks[first_worker_id]
            if first_worker_tasks:
                for first_worker_task in first_worker_tasks:
                    if first_worker_task['name'].endswith('embed_comments'):
                        results = {
                            "message" : "Embedding is already running",
                            "details" : first_worker_task
                        }
                        return results, 200

        t = embed_comments.delay()
        results = {
            "message" : "Embedding started.",
            "task.id" : t.id
        }

        return results, 200

@api.route('/tasks/running')
class RunningTasks(Resource):
    def get(self):

        i = celery_app.control.inspect()
        running_tasks = i.active()

        app.logger.debug(running_tasks)

        results = running_tasks

        return results, 200


@api.route('/tasks/abort')
class TasksAbort(Resource):
    @api.expect(tasks_model)
    def post(self):
        task_id = api.payload.get('task_id', None)

        i = celery_app.control.inspect()
        running_tasks = i.active()

        results = "There is no running task with id " + task_id
        if running_tasks:
            first_worker_id = [k for k in running_tasks.keys()][0]
            first_worker_tasks = running_tasks[first_worker_id]
            if first_worker_tasks:
                for first_worker_task in first_worker_tasks:
                    if first_worker_task['id'] == task_id:
                        # abortable_task = AbortableAsyncResult(task_id)
                        # abortable_task.abort()
                        celery_app.control.revoke(
                            task_id,
                            terminate = True
                        )
                        results = "Sent abort signal to task " + task_id

        return results, 200


# run app manually
if __name__ == "__main__":
    app.run(threaded = False)
