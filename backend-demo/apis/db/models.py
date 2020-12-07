import sys
from flask_restplus import Resource, Namespace
from psycopg2 import DatabaseError
from psycopg2.extras import RealDictCursor

from db import postgres_con
from db.queries import *

ns = Namespace('models', description="models api")


@ns.route('/<int:label_id>')
class Models(Resource):

    def get(self, label_id):

        cursor = postgres_con.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute(GET_MODEL_INFO(), (label_id,))
            postgres_con.commit()
        except DatabaseError:
            postgres_con.rollback()
            return {'msg': 'DatabaseError: transaction is aborted'}, 400

        results = cursor.fetchall()

        model_infos = []
        for model_info in results:
            print(model_info, file=sys.stderr)
            model_info['timestamp'] = model_info['timestamp'].isoformat()
            model_infos.append(model_info)

        return model_infos, 200
