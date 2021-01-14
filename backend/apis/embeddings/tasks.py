from http import HTTPStatus

import os
from flask_restplus import Resource, fields, Namespace
from requests import HTTPError

import core.tasks
from apis.service.embedding_service_client import EmbeddingServiceClient
from apis.utils.tasks import async_tasks
from config import settings
from embeddings.retrieve import RetrieveComment

ns = Namespace('embeddings', description="Embeddings-API namespace")

# db connection
try:
    default_source_id = 1
    retriever = RetrieveComment()
    retriever.load_index(default_source_id)
except:
    core.tasks.logger.error('DB connection failed.')
    exit(1)


sim_comments_model = ns.model('SimComments', {
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
id_model = ns.model('Id', {
    'ids': fields.List(
        fields.Integer,
        required=True,
        example=[200]
    )
})
sim_id_model = ns.model('SimId', {
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
url_model = ns.model('URL', {
    'service_url': fields.String(example='http://ltdemos.informatik.uni-hamburg.de/embedding-service'),
})


@ns.route('/get-service-url')
class GetServiceUrlRoute(Resource):
    def get(self):
        url = os.getenv('EMBEDDING_SERVICE_URL', settings.EMBEDDING_SERVICE_URL)
        return {'embedding service url': url}


@ns.route('/set-service-url')
class SetServiceUrlRoute(Resource):
    @ns.expect(url_model)
    def post(self):
        service_url = ns.payload.get('service_url', '')
        if service_url:
            os.environ['EMBEDDING_SERVICE_URL'] = service_url
            url = os.getenv('EMBEDDING_SERVICE_URL', settings.EMBEDDING_SERVICE_URL)
            return {'embedding service url': url}
        else:
            return "Empty url", HTTPStatus.BAD_REQUEST


@ns.route('/id')
class IdEmbedding(Resource):
    @ns.expect(id_model)
    def post(self):
        comments_id = ns.payload.get('ids', [])
        all_ids = [int(c) for c in comments_id]
        results = []
        for id in all_ids:
            embedding = retriever.get_embedding(id)
            results.append(embedding)
        return results, HTTPStatus.OK


@ns.route('/similar-ids')
class SimilarIds(Resource):
    @ns.expect(sim_id_model)
    def post(self):

        comments_ids = ns.payload.get('ids', [])

        source_id = ns.payload.get('source_id', 1)
        # ensure correct index is loaded for given source id
        if not retriever.load_index(source_id):
            return f"Error: could not find index for source_id {source_id}", HTTPStatus.BAD_REQUEST

        n = ns.payload.get('n', 10)
        if n == 0:
            n = 1
        results = []
        for _id in comments_ids:
            ids = retriever.get_nearest_for_id(_id, n=n)
            results.append(ids)

        return results, HTTPStatus.OK


@ns.route('/similar-comments')
class SimilarComments(Resource):
    @ns.expect(sim_comments_model)
    def post(self):
        comment_texts = ns.payload.get('comments', [])
        n = ns.payload.get('n', 10)

        source_id = ns.payload.get('source_id', 1)
        # ensure correct index is loaded for given source id
        if not retriever.load_index(source_id):
            return f"Error: could not find index for source_id {source_id}", HTTPStatus.BAD_REQUEST

        # get embedding
        try:
            embeddings = EmbeddingServiceClient().embed(comment_texts)
            results = []
            for embedding in embeddings:
                nn_ids = retriever.get_nearest_for_embedding(embedding)
                results.append([retriever.get_comment_text(id) for id in nn_ids])

            return results, HTTPStatus.OK
        except HTTPError:
            return '', HTTPStatus.INTERNAL_SERVER_ERROR


@ns.route('/source/<source_id>/embed')
class EmbedSource(Resource):
    def post(self, source_id):
        async_tasks.embeddings.embed(source_id)
        return '', HTTPStatus.NO_CONTENT


@ns.route('/source/<source_id>/index')
class IndexSource(Resource):
    def post(self, source_id):
        obs = async_tasks.embeddings.index(source_id)
        if obs is not None:
            obs.then(lambda: retriever.load_index(source_id, force_reload=True))

        return '', HTTPStatus.NO_CONTENT
