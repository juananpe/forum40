from flask import Flask
from logging.config import dictConfig
from flask_restplus import Api, Resource, fields
from core.proxy_wrapper import ReverseProxied
from BertFeatureExtractor import BertFeatureExtractor
from retrieve_comments import RetrieveComment
from index_comments import CommentIndexer
from embed_comments import CommentEmbedder

from celery import Celery
import os, logging

# pg config
pg_host = os.getenv('PG_HOST', 'postgres')
pg_port = os.getenv('PG_PORT', 5432)

# celery config
config_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
config_broker = "amqp://guest:guest@%s:5672//" % config_host

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

#load BERT model
app.logger.info('Loading BERT model')
be = BertFeatureExtractor(
    batch_size=8,
    device='cpu',
    keep_cls=False,
    use_layers=4,
    use_token=True
)
app.logger.info('BERT model loaded')

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


@api.route('/indexing')
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

@api.route('/embedding')
class EmbedComments(Resource):
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
                    if first_worker_task['name'].endswith('embed_comments'):
                        results = {
                            "message" : "Embedding is already running",
                            "details" : first_worker_task
                        }
                        return results, 200

        # start indexing
        t = embed_comments.delay()
        results = {
            "message" : "Embedding started.",
            "task.id" : t.id
        }

        app.logger.debug(i.active())

        return results, 200

@api.route('/running-tasks')
class RunningTasks(Resource):
    def get(self):

        i = celery_app.control.inspect()
        running_tasks = i.active()

        # import pdb
        # pdb.set_trace()

        app.logger.debug(running_tasks)

        results = running_tasks

        return results, 200


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)
    taskBase = celery.Task
    class ContextTask(taskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return taskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery


# celery config in Flask context
app.config['CELERY_BROKER_URL'] = config_broker
app.config['CELERY_BACKEND'] = 'rpc'
app.config['CELERY_TIMEZONE'] = 'CET'
celery_app = make_celery(app)


@celery_app.task
def index_comments(db_host = "postgres", db_port = 5432):

    # start indexing
    indexer = CommentIndexer(db_host, db_port)
    indexer.indexEmbeddings()

    return True


@celery_app.task
def embed_comments():

    ce = CommentEmbedder(embed_all=False, batch_size=8, host=pg_host, port=pg_port)
    ce.setExtractorModel(be)
    ce.setLogger(app.logger)

    # start embedding
    ce.embedComments()

    return True

# run app manually
if __name__ == "__main__":
    app.run(threaded = False)
