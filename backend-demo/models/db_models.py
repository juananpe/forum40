from flask_restplus import reqparse

aggregate_parser = reqparse.RequestParser()
aggregate_parser.add_argument('pipeline', type=list, default=dict(), location='json')
aggregate_parser.add_argument('options', type=dict, default=dict(), location='json')
