from apis.db import api
from flask_restplus import fields

obj_model = api.model('Object', { })

aggregate_model = api.model('Aggregate', {
    'pipeline': fields.List(fields.Nested(obj_model)),
    'options': fields.Nested(obj_model),
})