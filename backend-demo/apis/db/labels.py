from http import HTTPStatus

from flask_restplus import Resource, Namespace

from apis.utils.tasks import SingleProcessManager
from apis.utils.transformation import slice_dicts
from auth.token import token_required, TokenData
from db import with_database, Database
from db.db_models import label_parser_post

ns = Namespace('labels', description="labels api")

# pg config
process_manager = SingleProcessManager()
process_manager.register_process("init_facts", ["classification_update.py"])


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
            return {'msg': 'Label already exists.'}, HTTPStatus.CONFLICT

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

        return '', HTTPStatus.NO_CONTENT
