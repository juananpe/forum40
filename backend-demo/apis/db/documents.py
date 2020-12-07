from flask_restplus import Resource, Namespace
from psycopg2 import DatabaseError
from psycopg2.extras import RealDictCursor

from db import postgres_con, db_cursor
from db.db_models import document_parser
from db.queries import COUNT_DOCUMENTS, GET_COMMENTS_PER_CATEGORY
from jwt_auth.token import token_required

ns = Namespace('documents', description="documents api")


@ns.route('/count')
class DocumentsCount(Resource):
    def get(self):
        postgres = postgres_con.cursor()
        postgres.execute(COUNT_DOCUMENTS)
        db_return = postgres.fetchone()

        if db_return:
            return {'count': db_return[0]}, 200

        return {"msg": "Error"}, 400


def getDocumentByIds(id, external_id):
    query = f"select * from documents where source_id = '{id}' and external_id = '{external_id}'"
    postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
    try:
        postgres.execute(query)
        postgres_con.commit()

    except DatabaseError:
        postgres_con.rollback()
        return {'msg': 'DatabaseError: transaction is aborted'}, False

    return postgres.fetchone(), True


def getIdFromDoc(id, external_id):
    query = f"select id from documents where source_id = '{id}' and external_id = '{external_id}'"
    postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
    try:
        postgres.execute(query)
        postgres_con.commit()

    except DatabaseError:
        postgres_con.rollback()
        return {'msg': 'DatabaseError: transaction is aborted'}, False

    return postgres.fetchone(), True


@ns.route('/<id>/<external_id>')
class Documents(Resource):

    def get(self, id, external_id):
        sources, succ = getDocumentByIds(id, external_id)
        if not succ:
            return sources, 400

        if sources:
            sources['timestamp'] = sources['timestamp'].isoformat()
        return sources, 200


@ns.route('/categories/<source_id>/')
class Categories(Resource):
    def get(self, source_id):
        documents = []
        with db_cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(GET_COMMENTS_PER_CATEGORY, (source_id,))
            documents = cur.fetchall()

        result = {
            'names': [],
            'data': []
        }
        for d in documents:
            category = d['name']
            count = d['value']
            obj = {
                'value': count,
                'name': category
            }
            result['names'].append(category)
            result['data'].append(obj)

        return result, 200


@ns.route('/')
class DocumentsPost(Resource):
    @ns.expect(document_parser)
    @token_required
    @ns.doc(security='apikey')
    def post(self, data):
        args = document_parser.parse_args()
        url = args['url']
        title = args['title']
        text = args['text']
        timestamp = args['timestamp']
        metadata = args['metadata']
        if not metadata:
            metadata = ""
        source_id = args['source_id']
        external_id = args['external_id']

        sources, _ = getDocumentByIds(source_id, external_id)
        if sources:
            id, _ = getIdFromDoc(source_id, external_id)
            return id, 200

        postgres = postgres_con.cursor()
        insert_query = "INSERT INTO documents (url, title, text, timestamp, metadata, source_id, external_id) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;"

        try:
            postgres.execute(insert_query, (url, title, text, timestamp, metadata, source_id, external_id))
            postgres_con.commit()

        except DatabaseError:
            postgres_con.rollback()
            return {'msg': 'DatabaseError: transaction is aborted'}, 400

        added_source = postgres.fetchone()
        return {'id': added_source[0]}, 200
