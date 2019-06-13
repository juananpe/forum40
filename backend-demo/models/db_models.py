from apis.db import api
from flask_restplus import fields
from flask_restplus import reqparse

obj_model = api.model('Object', { })

aggregate_model = api.model('Aggregate', {
    'pipeline': fields.List(fields.Nested(obj_model)),
    'options': fields.Nested(obj_model),
})

label_time_model = api.model('Q', {
    'name': fields.String(default='personalstories'),
    'time_intervall': fields.Integer(default=36000000),
})

timeseries_parser_all = reqparse.RequestParser()
timeseries_parser_all.add_argument('time_intervall', type=int, default=36000000, required=True)

timeseries_parser = reqparse.RequestParser()
timeseries_parser.add_argument('label', action='append')
timeseries_parser.add_argument('time_intervall', type=int, default=36000000, required=True)

timeseries_parser_single = reqparse.RequestParser()
timeseries_parser_single.add_argument('label', required=True)
timeseries_parser_single.add_argument('time_intervall', type=int, default=36000000, required=True)

comments_model = api.model('Q', {
    'labelName': fields.String(default='personalstories'),
    'skip': fields.Integer(default=1),
    'limit': fields.Integer(default=50)
})

comments_parser_sl = reqparse.RequestParser()
comments_parser_sl.add_argument('label', action='append')
comments_parser_sl.add_argument('keyword', action='append')
comments_parser_sl.add_argument('skip', type=int, default=0, required=True)
comments_parser_sl.add_argument('limit', type=int, default=50, required=True)

comments_parser = reqparse.RequestParser()
comments_parser.add_argument('label', action='append')
comments_parser.add_argument('keyword', action='append')

