from http import HTTPStatus

import os
from flask_restplus import Resource, fields, Namespace, reqparse
from typing import Optional

import core.tasks
from apis.db.comments import load_annotations
from apis.utils.tasks import async_tasks
from auth.token import token_optional, TokenData
from config import settings
from db import with_database, Database
from db.repositories.comments import comment_fields
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

similar_model = reqparse.RequestParser()
similar_model.add_argument('n', type=int, default=10, help='Number of similar comments to retrieve')
similar_model.add_argument('label', action='append', type=int, default=lambda: [])

# API for comment ids
id_model = ns.model('Id', {
    'ids': fields.List(
        fields.Integer,
        required=True,
        example=[200]
    )
})

# API for service URL
url_model = ns.model('URL', {
    'service_url': fields.String(example='http://rzgpu1:5060/embed'),
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


@ns.route('/comments/<int:comment_id>/similar')
class SimilarComments(Resource):
    @token_optional
    @with_database
    @ns.expect(similar_model)
    def get(self, db: Database, token_data: Optional[TokenData], comment_id: int):
        args = similar_model.parse_args()

        query_comment = db.comments.find_by_id(comment_id, fields=comment_fields(metadata=True, embedding=True))
        retriever.load_index(query_comment['source_id'])

        nn_ids = retriever.get_nearest_for_embedding(query_comment['embedding'], args['n'])
        nn_comments = [
            db.comments.find_by_id(nn_id, fields=comment_fields(content=True, metadata=True))
            for nn_id in nn_ids
        ]
        load_annotations(
            db=db,
            comments=nn_comments,
            label_ids=args['label'],
            user_id=token_data['user_id'] if token_data is not None else None,
        )

        return nn_comments, HTTPStatus.OK


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
