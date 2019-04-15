from flask_restplus import Api, reqparse

api = Api(version='1.0', title='User-Comments-API', description="An API for usercomments")

#
# Parser Models
#
aggregate_parser = reqparse.RequestParser()
aggregate_parser.add_argument('pipeline', type=list, default=dict(), location='json')
aggregate_parser.add_argument('options', type=dict, default=dict(), location='json')
