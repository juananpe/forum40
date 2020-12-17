import os
from flask_restplus import Resource, Namespace

from apis.utils.tasks import SingleProcessManager
from apis.utils.transformation import slice_dicts
from db import with_database, Database
from db.db_models import label_parser_post
from jwt_auth.token import token_required, TokenData

ns = Namespace('labels', description="labels api")

# pg config
pg_host = os.getenv('PG_HOST', 'postgres')
pg_port = os.getenv('PG_PORT', '5432')

process_manager = SingleProcessManager(pg_host, pg_port)
process_manager.register_process("init_facts", ["classification_update.py", pg_host, pg_port])


@ns.route('/<int:source_id>')
class LabelsGetAll(Resource):
    @with_database
    def get(self, db: Database, source_id):
        labels = db.labels.find_all_by_source_id(source_id)
        return slice_dicts(labels, {'labels': 'name', 'ids': 'id', 'descriptions': 'description'})


@ns.route('/binary/<string:label_name>/<int:source_id>')
class AddLabel(Resource):
    @token_required
    @with_database
    @ns.doc(security='apikey')
    @ns.expect(label_parser_post)
    def put(self, db: Database, token_data: TokenData, label_name, source_id):
        if db.labels.is_name_taken(label_name):
            return {'msg': 'Label already exists.'}, 400

        args = label_parser_post.parse_args()

        db.labels.insert_label({
            'type': 'classification',
            'name': label_name,
            'source_id': source_id,
            'description': args['description'],
        })

        db.acc.commit()

        # init facts
        process_args = ["--labelname", label_name, "--init-facts-only"]
        process_manager.invoke("init_facts", str(source_id), process_args)
        print(f"Init facts for label {label_name} started as background process")

        return "ok", 200
