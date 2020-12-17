from flask_restplus import Resource, Namespace

from db import with_database, Database
from db.db_models import source_parser
from jwt_auth.token import token_required, token_optional

ns = Namespace('sources', description="sources api")


@ns.route('/')
class Sources(Resource):

    @token_optional
    @with_database
    @ns.doc(security='apikey')
    def get(self, db: Database):
        is_admin = self.get('role', None) == 'admin'
        sources = db.sources.find_all(include_protected=is_admin)
        return list(sources), 200

    @ns.expect(source_parser)
    @token_required
    @with_database
    @ns.doc(security='apikey')
    def post(self, db: Database, data):
        args = source_parser.parse_args()
        id_ = db.sources.insert(args)
        return {'id': id_}, 200


@ns.route('/<name>')
class SourcesByName(Resource):
    @with_database
    def get(self, db: Database, name):
        source = db.sources.find_by_name(name)
        if source is None:
            return '', 404

        return source, 200
