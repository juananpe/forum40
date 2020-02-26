import os
import requests

from flask_restplus import Resource, fields
from flask import current_app

from apis.embeddings import api
from config import settings

from embeddings_retrieve import RetrieveComment
from apis.utils.tasks import SingleProcessManager

ns = api.namespace('embeddings', description="Embeddings-API namespace")

# pg config
pg_host = os.getenv('PG_HOST', 'postgres')
pg_port = os.getenv('PG_PORT', '5432')

process_manager = SingleProcessManager(pg_host, pg_port)
process_manager.register_process("indexing", ["embeddings_index.py", pg_host, pg_port])
process_manager.register_process("embedding", ["embeddings_embed.py", pg_host, pg_port])

# db connection
try:
    retriever = RetrieveComment(pg_host, pg_port)
except:
    current_app.logger.error('DB connection failed.')
    exit(1)


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


@ns.route('/get-service-url')
class GetServiceUrlRoute(Resource):
    def get(self):
        return {'embedding service url': settings.EMBEDDING_SERVICE_URL}


@ns.route('/id')
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


@ns.route('/similar-ids')
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


@ns.route('/similar-comments')
class SimilarComments(Resource):
    @api.expect(sim_comments_model)
    def post(self):
        comment_texts = api.payload.get('comments', [])
        n = api.payload.get('n', 10)

        # get embedding
        embeddings, status = get_embeddings(comment_texts)
        if not status:
            return {'message' : embeddings}, 500
        results = []
        for embedding in embeddings:
            nn_ids = retriever.get_nearest_for_embedding(embedding)
            results.append([retriever.get_comment_text(id) for id in nn_ids])
        return results, 200


@ns.route('/tasks')
class Tasks(Resource):
    def get(self):
        results = process_manager.tasks()
        return results, 200


@ns.route('/tasks/<taskname>')
class TaskStatus(Resource):
    def get(self, taskname):
        results = process_manager.status(taskname)
        return results, 200


@ns.route('/tasks/<taskname>/invoke')
class TaskInvoke(Resource):
    def get(self, taskname):
        results = process_manager.invoke(taskname)
        return results, 200


@ns.route('/tasks/<taskname>/abort')
class TaskAbort(Resource):
    def get(self, taskname):
        results = process_manager.abort(taskname)
        return results, 200

@ns.route('/tasks/clear')
class TasksClear(Resource):
    def get(self):
        results = process_manager.clear()
        return results, 200


def get_embeddings(string_list):

    response = requests.post(
        settings.EMBEDDING_SERVICE_URL,
        json={"texts" : string_list},
        headers={'Accept': 'application/json', 'Content-Type': 'application/json'}
    )

    if response.ok:
        return response.json(), True
    else:
        return response.reason(), False
