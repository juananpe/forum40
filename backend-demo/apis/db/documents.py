from flask_restplus import Resource, Namespace

from db import Database, with_database
from db.db_models import document_parser
from jwt_auth.token import token_required, TokenData

ns = Namespace('documents', description="documents api")


@ns.route('/categories/<source_id>/')
class Categories(Resource):
    @with_database
    def get(self, db: Database, source_id):
        category_comments = db.comments.count_by_category_for_source(source_id)

        result = {
            'names': [entry['category_name'] for entry in category_comments],
            'data': [
                {'name': entry['category_name'], 'value': entry['comment_count']}
                for entry in category_comments
            ],
        }

        return result, 200


@ns.route('/')
class DocumentsPost(Resource):
    @token_required
    @with_database
    @ns.expect(document_parser)
    @ns.doc(security='apikey')
    def post(self, db: Database, token_data: TokenData):
        args = document_parser.parse_args()
        source_id = args['source_id']
        external_id = args['external_id']

        if (id_ := db.documents.find_id_by_external_id(source_id, external_id)) is not None:
            return {'id': id_}, 409

        id_ = db.documents.insert(args)

        return {'id': id_}, 200
