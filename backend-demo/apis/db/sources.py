from http import HTTPStatus

from typing import Optional

from flask_restplus import Resource, Namespace

from db import with_database, Database
from db.db_models import source_parser
from jwt_auth.token import token_required, token_optional, TokenData

ns = Namespace('sources', description="sources api")


@ns.route('/')
class Sources(Resource):

    @token_optional
    @with_database
    @ns.doc(security='apikey')
    def get(self, db: Database, token_data: Optional[TokenData]):
        is_admin = token_data is not None and token_data['role'] == 'admin'
        sources = db.sources.find_all(include_protected=is_admin)
        return list(sources), HTTPStatus.OK

    @token_required
    @with_database
    @ns.expect(source_parser)
    @ns.doc(security='apikey')
    def post(self, db: Database, token_data: TokenData):
        args = source_parser.parse_args()
        id_ = db.sources.insert(args)
        return {'id': id_}, HTTPStatus.OK


@ns.route('/<name>')
class SourcesByName(Resource):
    @with_database
    def get(self, db: Database, name):
        source = db.sources.find_by_name(name)
        if source is None:
            return '', HTTPStatus.NOT_FOUND

        return source, HTTPStatus.OK
