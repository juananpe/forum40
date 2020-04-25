import os

from flask import Flask
from logging.config import dictConfig
from flask_restplus import Api, Resource, fields
from core.proxy_wrapper import ReverseProxied
from classification_classifier import get_history_path

from apis.classification import api

from apis.utils.tasks import SingleProcessManager

ns = api.namespace('classification', description="Classification-API namespace")

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


update_model = api.model('update', {
    'source_id': fields.Integer(
        description="Source id",
        required=True,
        example=1
    ),
    'labelname': fields.String(
        description = 'Labelname to update model and machine classification.',
        example = 'SentimentNegative',
        required = True
    ),
    'optimize' : fields.Boolean(
        description = 'Perform hyperparameter optimization',
        default = False,
        required = False
    ),
    'skip-confidence' : fields.Boolean(
        description = 'Fast version only updates changing labels, but not confidence scores',
        default = False,
        required = False
    )
})

history_model = api.model('history', {
    'labelname': fields.String(
        description = 'Labelname to update model and machine classification.',
        example = 'SentimentNegative',
        required = True
    ),
    'n' : fields.Integer(
        description = 'Number of history entries',
        example = 100,
        required = False
    )
})


@ns.route('/update')
class ClassifierService(Resource):
    @api.expect(update_model)
    def post(self):
        source_id = api.payload.get('source_id', None)
        labelname = api.payload.get('labelname', None)
        optimize = api.payload.get('optimize', False)
        skip_confidence = api.payload.get('skip-confidence', False)
        if labelname and source_id:
            args = ["--labelname", labelname]
            if skip_confidence:
                args.append("--skip-confidence")
            if optimize:
                args.append("--optimize")
            results = process_manager.invoke("update", str(source_id), args)
            return results, 200
        else:
            return {'error' : 'Something went wrong.'}, 500


@ns.route('/status')
class StatusService(Resource):
    def get(self):
        results = process_manager.status("update")
        return results, 200


@ns.route('/abort')
class AbortService(Resource):
    def get(self):
        results = process_manager.abort("update")
        return results, 200

@ns.route('/history')
class HistoryService(Resource):
    @ns.expect(history_model)
    def post(self):
        labelname = api.payload.get('labelname', None)
        n = api.payload.get('n', 100)
        if labelname:
            try:
                history = []
                with open(get_history_path(labelname), 'r') as f:
                    for line in f:
                        history.append(line.strip())
                history = history[-n:]
                results = {
                    'labelname' : labelname,
                    'history' : history
                }
                return results, 200
            except:
                return {'error': 'Something went wrong.'}, 500
        else:
            return {'error' : 'No labelname given.'}, 404

