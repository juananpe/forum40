from http import HTTPStatus

import os
from flask_restplus import Resource, fields, Namespace
from logging.config import dictConfig

from apis.utils.tasks import SingleProcessManager
from classification_classifier import get_history_path

ns = Namespace('classification', description="Classification-API namespace")

# pg config
pg_host = os.getenv('PG_HOST', 'postgres')
pg_port = os.getenv('PG_PORT', '5432')

process_manager = SingleProcessManager(pg_host, pg_port)
process_manager.register_process("train", ["classification_train.py", pg_host, pg_port])
process_manager.register_process("update", ["classification_update.py", pg_host, pg_port])

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi']
    }
})


update_model = ns.model('update', {
    'source_id': fields.Integer(
        description="Source id",
        required=True,
        example=1
    ),
    'labelname': fields.String(
        description='Labelname to update model and machine classification.',
        example='SentimentNegative',
        required=True
    ),
    'optimize': fields.Boolean(
        description='Perform hyperparameter optimization',
        default=False,
        required=False
    ),
    'neural-network': fields.Boolean(
        description='Indicate whether train the model with neural network',
        default=False,
        required=False
    ),
    'skip-confidence': fields.Boolean(
        description='Fast version only updates changing labels, but not confidence scores',
        default=False,
        required=False
    ),
    'skip-training': fields.Boolean(
        description='Indicate whether training should be skipped',
        default=False,
        required=False
    )
})

history_model = ns.model('history', {
    'labelname': fields.String(
        description='Labelname to update model and machine classification.',
        example='SentimentNegative',
        required=True
    ),
    'n': fields.Integer(
        description='Number of history entries',
        example=100,
        required=False
    )
})


@ns.route('/update')
class ClassifierService(Resource):
    @ns.expect(update_model)
    def post(self):
        source_id = ns.payload.get('source_id', None)
        labelname = ns.payload.get('labelname', None)
        optimize = ns.payload.get('optimize', False)
        neural_network = ns.payload.get('neural-network', False)
        skip_training = ns.payload.get('skip-training', False)
        skip_confidence = ns.payload.get('skip-confidence', False)
        if labelname and source_id:
            args = ["--labelname", labelname]
            if skip_confidence:
                args.append("--skip-confidence")
            if optimize:
                args.append("--optimize")
            if skip_training:
                args.append("--skip-train")
            if neural_network:
                args.append("--nn")
            results = process_manager.invoke("update", str(source_id), args)
            return results, HTTPStatus.OK
        else:
            return {'error': 'Something went wrong.'}, HTTPStatus.INTERNAL_SERVER_ERROR


@ns.route('/status')
class StatusService(Resource):
    def get(self):
        results = process_manager.status("update")
        return results, HTTPStatus.OK


@ns.route('/abort')
class AbortService(Resource):
    def get(self):
        results = process_manager.abort("update")
        return results, HTTPStatus.OK


@ns.route('/history')
class HistoryService(Resource):
    @ns.expect(history_model)
    def post(self):
        labelname = ns.payload.get('labelname', None)
        n = ns.payload.get('n', 100)
        if labelname:
            try:
                history = []
                with open(get_history_path(labelname), 'r') as f:
                    for line in f:
                        history.append(line.strip())
                history = history[-n:]
                results = {
                    'labelname': labelname,
                    'history': history
                }
                return results, HTTPStatus.OK
            except:
                return {'error': 'Something went wrong.'}, HTTPStatus.INTERNAL_SERVER_ERROR
        else:
            return {'error': 'No labelname given.'}, HTTPStatus.NOT_FOUND
