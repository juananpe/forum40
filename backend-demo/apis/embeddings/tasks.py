import os

from flask_restplus import Resource, fields
from flask import current_app

from apis.embeddings import api
from config import settings

from embeddings_retrieve import RetrieveComment
from apis.utils.tasks import SingleProcessManager, get_embeddings

ns = api.namespace('embeddings', description="Embeddings-API namespace")

# pg config
pg_host = os.getenv('PG_HOST', 'postgres')
pg_port = os.getenv('PG_PORT', '5432')

process_manager = SingleProcessManager(pg_host, pg_port)
process_manager.register_process("indexing", ["embeddings_index.py", pg_host, pg_port])
process_manager.register_process("embedding", ["embeddings_embed.py", pg_host, pg_port])

# db connection
try:
    default_source_id = 1
    retriever = RetrieveComment(pg_host, pg_port)
    retriever.load_index(default_source_id)
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
    ),
    'source_id': fields.Integer(
        description="Source id",
        required=True,
        example=1
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
    ),
    'source_id': fields.Integer(
        description="Source id",
        required=True,
        example=1
    )
})



# API for service URL
url_model = api.model('URL', {
    'service_url': fields.String(example = 'http://ltdemos.informatik.uni-hamburg.de/embedding-service'),
})


@ns.route('/get-service-url')
class GetServiceUrlRoute(Resource):
    def get(self):
        url = os.getenv('EMBEDDING_SERVICE_URL', settings.EMBEDDING_SERVICE_URL)
        return {'embedding service url': url}

@ns.route('/set-service-url')
class SetServiceUrlRoute(Resource):
    @api.expect(url_model)
    def post(self):
        service_url = api.payload.get('service_url', '')
        if service_url:
            os.environ['EMBEDDING_SERVICE_URL'] = service_url
            url = os.getenv('EMBEDDING_SERVICE_URL', settings.EMBEDDING_SERVICE_URL)
            return {'embedding service url': url}
        else:
            return "Empty url", 400

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

        source_id = api.payload.get('source_id', 1)
        # ensure correct index is loaded for given source id
        if not retriever.load_index(source_id):
            return "Error: could not find index for source_id %d" % source_id, 400

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

        source_id = api.payload.get('source_id', 1)
        # ensure correct index is loaded for given source id
        if not retriever.load_index(source_id):
            return "Error: could not find index for source_id %d" % source_id, 400

        # get embedding
        embeddings, status = get_embeddings(comment_texts)
        if not status:
            return {'message' : embeddings}, 500
        results = []
        for embedding in embeddings:
            nn_ids = retriever.get_nearest_for_embedding(embedding)
            results.append([retriever.get_comment_text(id) for id in nn_ids])

        return results, 200

@ns.route('/reload-index/<source_id>')
class ReloadIndex(Resource):
    def get(self, source_id):
        if not retriever.load_index(source_id, force_reload = True):
            return "Error: could not find index for source_id %s" % source_id, 400
        else:
            return "Index for source id %s reloaded" % source_id, 200


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


@ns.route('/tasks/<taskname>/invoke/<source_id>')
class TaskInvoke(Resource):
    def get(self, taskname, source_id):
        results = process_manager.invoke(taskname, source_id)
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

