from apis.db import api
from flask_restplus import fields

obj_model = api.model('Object', { })

aggregate_model = api.model('Aggregate', {
    'pipeline': fields.List(fields.Nested(obj_model)),
    'options': fields.Nested(obj_model),
})

label_time_model = api.model('Q', {
    'id': fields.String(default='5cac4dadbbf6b808fc6f5e0b'),
    'time_intervall': fields.Integer(default=36000000),
})