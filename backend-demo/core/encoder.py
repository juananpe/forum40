from json import JSONEncoder
import datetime
from bson.objectid import ObjectId

class JSONMongoEncoder(JSONEncoder):
    ''' extend json-encoder class'''

    def default(self, o): # pylint bug @see https://github.com/PyCQA/pylint/issues/414
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime.datetime):
            return str(o)
        return JSONEncoder.default(self, o)