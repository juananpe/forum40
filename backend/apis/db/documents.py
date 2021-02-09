from http import HTTPStatus

from flask_restplus import Resource, Namespace
from typing import Optional

from auth.token import token_required, token_optional, TokenData, allow_access_source_id
from db import Database, with_database
from db.db_models import document_parser, document_list_parser
from db.repositories.documents import document_fields

ns = Namespace('documents', description="documents api")


@ns.route('/categories/<source_id>/')
class Categories(Resource):
    @with_database
    def get(self, db: Database, source_id):
        category_comments = list(db.comments.count_by_category_for_source(source_id))

        result = {
            'names': [entry['category_name'] for entry in category_comments],
            'data': [
                {'name': entry['category_name'], 'value': entry['comment_count']}
                for entry in category_comments
            ],
        }

        return result, HTTPStatus.OK


@ns.route('/')
class DocumentsRoot(Resource):
    @token_optional
    @with_database
    @ns.expect(document_list_parser)
    @ns.doc(security='apikey')
    def get(self, db: Database, token_data: Optional[TokenData]):
        args = document_list_parser.parse_args()
        if not allow_access_source_id(args['source_id'], token_data):
            return '', HTTPStatus.FORBIDDEN

        return list(db.documents.find_all_by_source_id(
            source_id=args['source_id'],
            limit=args['limit'],
            skip=args['skip'],
            fields=document_fields(metadata=True) | {'title'},
        ))

    @token_required
    @with_database
    @ns.expect(document_parser)
    @ns.doc(security='apikey')
    def post(self, db: Database, token_data: TokenData):
        args = document_parser.parse_args()

        if (id_ := db.documents.find_id_by_external_id(args['source_id'], args['external_id'])) is not None:
            return {'id': id_}, HTTPStatus.CONFLICT

        id_ = db.documents.insert(args)

        return {'id': id_}, HTTPStatus.OK
