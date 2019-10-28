import os

from flask import Flask
from logging.config import dictConfig
from flask_restplus import Api, Resource, fields
from core.proxy_wrapper import ReverseProxied
from update import LabelUpdater
from train import ClassifierTrainer
from classifier import get_history_path

from utils.tasks import SingleProcessManager

# pg config
pg_host = os.getenv('PG_HOST', 'postgres')
pg_port = os.getenv('PG_PORT', '5432')

process_manager = SingleProcessManager(pg_host, pg_port)


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


# define app
app = Flask(__name__)
app.wsgi_app = ReverseProxied(app.wsgi_app)


# define API
api = Api(app, version='0.1', title='Classification-API',
          description="An API for classifying user comments")

update_model = api.model('update', {
    'labelname': fields.String(
        description = 'Labelname to update model and machine classification.',
        example = 'SentimentNegative',
        required = True
    ),
    'optimize' : fields.Boolean(
        description = 'Perform hyperparameter optimization',
        example = False,
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


@api.route('/update')
class ClassifierService(Resource):
    @api.expect(update_model)
    def post(self):
        labelname = api.payload.get('labelname', None)
        if labelname:
            results = process_manager.invoke("update", ["--labelname", labelname])
            return results, 200
        else:
            return {'error' : 'Something went wrong.'}, 500


@api.route('/status')
class StatusService(Resource):
    def get(self):
        results = process_manager.status("update")
        return results, 200


@api.route('/abort')
class AbortService(Resource):
    def get(self):
        results = process_manager.abort("update")
        return results, 200

@api.route('/history')
class HistoryService(Resource):
    @api.expect(history_model)
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


# run app manually
if __name__ == "__main__":
    app.run(threaded = True)
