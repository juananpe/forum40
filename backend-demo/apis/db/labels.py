import os
from flask_restplus import Resource, Namespace

from apis.utils.tasks import SingleProcessManager
from apis.utils.transformation import slice_dicts
from db import postgres_con, with_database, Database
from db.db_models import label_parser_post
from db.queries import *
from jwt_auth.token import token_required

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
        labels = list(db.labels.find_all_by_source_id(source_id))
        return slice_dicts(labels, {'labels': 'name', 'ids': 'id', 'descriptions': 'description'})


@ns.route('/binary/<string:label_name>/<int:source_id>')
class AddLabel(Resource):
    @token_required
    @ns.doc(security='apikey')
    @ns.expect(label_parser_post)
    def put(self, data, label_name, source_id):
        postgres = postgres_con.cursor()
        postgres.execute(COUNT_LABELS_BY_NAME(label_name))
        db_result = postgres.fetchone()

        args = label_parser_post.parse_args()
        description = args.get('description', None)

        if db_result:
            if db_result[0] >= 1:
                return {'msg': 'Label already exists.'}, 400

        postgres.execute(SELECT_MAX_ID('labels'))
        max_id = postgres.fetchone()[0]

        label_id = max_id + 1

        postgres.execute(INSERT_LABEL, (label_id, 'classification', label_name, source_id, description))
        postgres_con.commit()

        # init facts
        args = ["--labelname", label_name, "--init-facts-only"]
        results = process_manager.invoke("init_facts", str(source_id), args)
        print(f"Init facts for label {label_name} started as background process")

        return "ok", 200
