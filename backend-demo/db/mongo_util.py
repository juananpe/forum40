import json
from bson import json_util


def aggregate(coll, body):
    pipeline = [{ "$limit": 10}] # TODO set as default value
    options = {}
    tmp = body['pipeline']
    if tmp and len(tmp) and len(tmp[0]):
        pipeline = body['pipeline']
    if body['options']:
        options = body['options']

    cursor = list(coll.aggregate(pipeline, options))
    return json_util.dumps(cursor)