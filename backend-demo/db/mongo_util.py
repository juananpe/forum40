import json
from bson import json_util


def aggregate(coll, body):
    pipeline = []
    options = {}
    if body['pipeline']:
        pipeline = body['pipeline']
    if body['options']:
        options = body['options']

    cursor = list(coll.aggregate(pipeline, options))
    return json_util.dumps(cursor)