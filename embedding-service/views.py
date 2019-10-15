from flask_restplus import Api, Resource, fields

from app import app, huey
from tasks import index_comments, embed_comments

from huey.exceptions import TaskLockedException




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

        try:
            # start indexing
            t = embed_comments()
            results = {
                "message": "Embedding started.",
                "task.id": t.id
            }
        except TaskLockedException as e:
            results = {
                "message": "Embedding is already running."
            }

        return results, 200

@api.route('/running-tasks')
class RunningTasks(Resource):
    def get(self):

        results = huey.pending()

        return results, 200
