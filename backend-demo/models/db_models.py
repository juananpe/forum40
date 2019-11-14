from flask_restplus import reqparse
from datetime import datetime

groupByModel = reqparse.RequestParser()
groupByModel.add_argument('label', type=int)
groupByModel.add_argument('keyword', action='append')

comments_parser_sl = reqparse.RequestParser()
comments_parser_sl.add_argument('label', action='append')
comments_parser_sl.add_argument('keyword', action='append')
comments_parser_sl.add_argument('source_id', action='append')
comments_parser_sl.add_argument('skip', type=int, default=0, required=True)
comments_parser_sl.add_argument('limit', type=int, default=50, required=True)

comments_parser = reqparse.RequestParser()
comments_parser.add_argument('label', action='append')
comments_parser.add_argument('keyword', action='append')
comments_parser.add_argument('source_id', action='append')

comment_parser = reqparse.RequestParser()
comment_parser.add_argument('label', action='append')

source_parser = reqparse.RequestParser()
source_parser.add_argument('name', required=True)
source_parser.add_argument('domain', required=True)

comment_parser_post = reqparse.RequestParser()
# id
comment_parser_post.add_argument('doc_id', default="")
comment_parser_post.add_argument('source_id', required=True, default="")
comment_parser_post.add_argument('user_id', default="")
comment_parser_post.add_argument('parent_comment_id', default="")
comment_parser_post.add_argument('status', default="")
comment_parser_post.add_argument('title', required=True, default="")
comment_parser_post.add_argument('text', required=True, default="")
comment_parser_post.add_argument('embedding', default=None)
comment_parser_post.add_argument('timestamp', required=True, type=lambda x: datetime.strptime(
    x, '%Y-%m-%dT%H:%M:%S'))
