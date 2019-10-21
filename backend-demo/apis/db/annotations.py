from flask import request
from flask_restplus import Resource, reqparse, fields
from apis.db import api

from psycopg2.extras import RealDictCursor

from db import postgres_con

from db.queries import *
from psycopg2 import DatabaseError

from jwt_auth.token import token_required

from models.db_models import comments_parser_sl

ns = api.namespace('annotations', description="annotations api")

@ns.route('/count')
class SourcesCount(Resource):
    def get(self):
        postgres = postgres_con.cursor()

        try:        
            postgres.execute(COUNT_ANNOTATIONS)
        except DatabaseError:
            postgres_con.rollback()
            return {'msg' : 'DatabaseError: transaction is aborted'}, 400

        db_return = postgres.fetchone()

        if db_return:
             return {'count': db_return[0]}, 200
        
        return {"msg": "Error"}, 400

@ns.route('/<int:comment_id>')
class GetLabel(Resource):
    def get(self, comment_id):
        postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
        try:        
            postgres.execute(f"SELECT label_id, user_id, label FROM Annotations WHERE comment_id = {comment_id}")
        except DatabaseError:
            postgres_con.rollback()
            return {'msg' : 'DatabaseError: transaction is aborted'}, 400

        db_return = postgres.fetchall()
        return db_return


@ns.route('/user/<int:user_id>')
@api.expect(comments_parser_sl)
class GetLabelUser(Resource):
    def get(self, user_id):

        args = comments_parser_sl.parse_args()
        skip = args["skip"]
        limit = args["limit"]

        annotations_where_sec = ''
        if 'label' in args and args['label']:
            labelIds = ' WHERE label_id IN ({0})'.format(", ".join(i for i in args['label']))
            annotations_where_sec += labelIds

        comments_where_sec = ''
        if 'keyword' in args and args['keyword']:
            searchwords = ' OR '.join("text LIKE '%{0}%'".format(x) for x in args['keyword'])
            comments_where_sec += 'WHERE ' +  searchwords

        postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
        query = f"""
            SELECT _.id, array_agg(_.agg) as group_annotation FROM
            (
                SELECT c.id, ARRAY[a.label_id, a.label::int] as agg
                    FROM (SELECT * FROM comments {comments_where_sec} LIMIT {limit} OFFSET {skip}) AS c 
                    LEFT OUTER JOIN 
                    (SELECT * FROM annotations {annotations_where_sec}) AS a
                    ON c.id = a.comment_id
                    WHERE a.user_id = '{user_id}'
                    GROUP BY c.id, a.label_id, a.label
            ) _ 
            GROUP BY _.id
        """

        try:        
            postgres.execute(query)
        except DatabaseError:
            postgres_con.rollback()
            return {'msg' : 'DatabaseError: transaction is aborted'}, 400

        db_return = postgres.fetchall()
        return db_return


@ns.route('/group/')
@api.expect(comments_parser_sl)
class GetLabelGroup(Resource):
    def get(self):

        args = comments_parser_sl.parse_args()
        skip = args["skip"]
        limit = args["limit"]

        annotations_where_sec = ''
        if 'label' in args and args['label']:
            labelIds = ' WHERE label_id IN ({0})'.format(", ".join(i for i in args['label']))
            annotations_where_sec += labelIds

        comments_where_sec = ''
        if 'keyword' in args and args['keyword']:
            searchwords = ' OR '.join("text LIKE '%{0}%'".format(x) for x in args['keyword'])
            comments_where_sec += 'WHERE ' +  searchwords


        postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
        query = f"""
        SELECT _.id, array_agg(_.agg) as group_annotation FROM
        (
            SELECT c.id, ARRAY[a.label_id, count(a.label or null), count(not a.label or null)] as agg
                FROM (SELECT * FROM comments {comments_where_sec} LIMIT {limit} OFFSET {skip}) AS c 
                LEFT OUTER JOIN 
                (SELECT * FROM annotations {annotations_where_sec}) AS a
                ON c.id = a.comment_id
                GROUP BY c.id, a.label_id, c.title, c.text, c.timestamp
        ) _ 
        GROUP BY _.id
        """

        try:        
            postgres.execute(query)
        except DatabaseError:
            postgres_con.rollback()
            return {'msg' : 'DatabaseError: transaction is aborted'}, 400

        db_return = postgres.fetchall()
        return db_return

def _comment_exists(id):
    postgres = postgres_con.cursor()
    postgres.execute(SELECT_COMMENT_BY_ID(id))
    db_result = postgres.fetchone()
    return db_result != None

def _label_exists(id):
    postgres = postgres_con.cursor()
    postgres.execute(SELECT_LABEL_BY_ID(id))
    db_result = postgres.fetchone()
    return db_result != None

def _user_exists(id):
    postgres = postgres_con.cursor()
    postgres.execute(SELECT_USER_BY_ID(id))
    db_result = postgres.fetchone()
    return db_result != None

import sys

import sys

@ns.route('/<int:comment_id>/<int:label_id>/<int:label>')
class LabelComment(Resource):
    @token_required
    @api.doc(security='apikey')
    def put(self, data, comment_id ,label_id, label):

        user_id = self["user"]
        label = bool(label)

        try: 
            # Check Args
            if not _comment_exists(comment_id):
                return {"msg": "No Comments with id: {0}".format(comment_id)}, 400

            if not _label_exists(label_id):
                return {"msg": "No Label with id: {0}".format(label_id)}, 400

            if not _user_exists(user_id):
                return {"msg": "No User with id: {0}".format(user_id)}, 400
        except DatabaseError:
            postgres_con.rollback()
            return {'msg' : 'DatabaseError: transaction is aborted'}, 400

        postgres = postgres_con.cursor(cursor_factory=RealDictCursor)
        
        try:        
            postgres.execute(SELECT_LABEL_FROM_ANNOTATIONS_BY_IDS(label_id, comment_id, user_id))
        except DatabaseError:
            postgres_con.rollback()
            return {'msg' : 'DatabaseError: transaction is aborted'}, 400

        db_result = postgres.fetchone()

        if not db_result: # No Annotation found
            try:        
                postgres.execute(INSERT_ANNOTATION(label_id, comment_id, user_id, label))
            except DatabaseError:
                postgres_con.rollback()
                return {'msg' : 'DatabaseError: transaction is aborted'}, 400

        elif db_result['label'] != label: # Update
            try:        
                postgres.execute(UPDATE_ANNOTATION(label_id, comment_id, user_id, label))
            except DatabaseError:
                postgres_con.rollback()
                return {'msg' : 'DatabaseError: transaction is aborted'}, 400
        else: 
            pass

        postgres_con.commit()

        return "ok", 200