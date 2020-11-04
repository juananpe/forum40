from flask import request
from flask_restplus import Resource, reqparse

from apis.db import api
from db.queries import COUNT_DOCUMENTS, GET_CATEGORIES
from db import postgres_con, db_cursor
from db.db_models import document_parser
from jwt_auth.token import token_required
from psycopg2 import DatabaseError
from psycopg2.extras import RealDictCursor

ns = api.namespace('documents', description="documents api")

#document_parser = reqparse.RequestParser()
#document_parser.add_argument('id', required=True)
#document_parser.add_argument('url', required=True)
#document_parser.add_argument('title', required=True)
#document_parser.add_argument('text', required=True)
#document_parser.add_argument('timestamp', required=True)
#document_parser.add_argument('metadata', default="")
#document_parser.add_argument('source_id', required=True)
#document_parser.add_argument('external_id', required=True)

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

        # 1. get all documents
        #.2. map [document_id: category]
        # 3. laufen über alle commententare von der source_id
        # 4. zählen

        GET_ALL_DOCUMENTS = "SELECT id, cast(metadata as json) -> 'author' -> 'departments'->>0 AS category FROM documents WHERE source_id = %s"
        documents = []
        document_id_to_category = {}
        with db_cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(GET_ALL_DOCUMENTS, (source_id,))
            documents = cur.fetchall()
        
        for d in documents:
            document_id_to_category[d['id']] = d['category']

        comments = []
        with db_cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT doc_id FROM comments c WHERE c.source_id = %s', (source_id,))
            comments = cur.fetchall()

        comments_count = {}
        for c in comments:
            document_id = c['doc_id']
            comment_category = document_id_to_category[document_id]
            current_count = comments_count.get(comment_category, 0) + 1
            comments_count[comment_category] = current_count

        result = {
            'names': [],
            'data': []
        }
        for category,count in comments_count.items():
            obj = {
                'value': count,
                'name' : category
            }
            result['names'].append(category)
            result['data'].append(obj)

        return result, 200

@ns.route('/')
class DocumentsPost(Resource):
    @api.expect(document_parser)
    @token_required
    @api.doc(security='apikey')
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