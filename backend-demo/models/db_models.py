from apis.db import api
from flask_restplus import fields

obj_model = api.model('Object', { })

aggregate_model = api.model('Aggregate', {
    'pipeline': fields.List(fields.Nested(obj_model)),
    'options': fields.Nested(obj_model),
})

label_time_model = api.model('Q', {
    'name': fields.String(default='personalstories'),
    'time_intervall': fields.Integer(default=36000000),
})

comments_model = api.model('Q', {
    'labelName': fields.String(default='personalstories'),
    'skip': fields.Integer(default=0),
    'limit': fields.Integer(default=50)
})