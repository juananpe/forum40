import json
from bson import json_util


def aggregate(coll, body):
    pipeline = []
    options = {}
    if body['pipeline']:
        pipeline = body['pipeline']
    if body['options']:
        options = body['options']

    cursor = coll.aggregate(pipeline, options)
    res = [json.dumps(doc, default=json_util.default) for doc in cursor]
    return res