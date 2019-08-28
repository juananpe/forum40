from flask import Flask
from logging.config import dictConfig
from flask_restplus import Api, Resource, fields
from core.proxy_wrapper import ReverseProxied
from updateLabel import *

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
    'labelname': fields.String('Labelname to update model and machine classification.')
})


@api.route('/update')
class ClassifierService(Resource):
    @api.expect(update_model)
    def post(self):
        labelname = api.payload.get('labelname', None)
        if labelname:
            labelUpdater = LabelUpdater(labelname)
            labelUpdater.updateLabels()
            results = {'info' : 'Started update of label ' + labelname}
            return results, 200
        else:
            return {'error' : 'Something went wrong.'}, 500


# run app manually
if __name__ == "__main__":
    app.run(threaded = True)
