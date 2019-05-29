from functools import wraps
from flask import request, jsonify
import jwt

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return {'message' : 'Token is missing.'}, 401

        try:
            data = jwt.decode(token, 'eh9Df9G27gahgHJ7g2oGQz6Ug5he6ud5shd') # TODO hide pwd
            # TODO check if data is ok
        except: 
            return {'message' : 'Token is invalid.'}, 401

        return f(*args, **kwargs)

    return decorated