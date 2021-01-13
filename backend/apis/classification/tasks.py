from http import HTTPStatus

from flask_restplus import Resource, fields, Namespace
from logging.config import dictConfig

from apis.utils.tasks import async_tasks
from classification.classifier import get_history_path

ns = Namespace('classification', description="Classification-API namespace")

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
        async_tasks.classification.update(
            source_id=ns.payload.get('source_id', None),
            labelname=ns.payload.get('labelname', None),
            skip_confidence=ns.payload.get('skip-confidence', False),
            optimize=ns.payload.get('optimize', False),
            init_facts_only=False,
            skip_train=ns.payload.get('skip-training', False),
        )
        return '', HTTPStatus.NO_CONTENT


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
