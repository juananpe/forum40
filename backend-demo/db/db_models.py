from flask_restplus import reqparse
from datetime import datetime

groupByModel = reqparse.RequestParser()
groupByModel.add_argument('label', type=int)
groupByModel.add_argument('keyword', action='append')
groupByModel.add_argument('source_id', type=int, default=1)

comments_parser_sl = reqparse.RequestParser()
comments_parser_sl.add_argument('label', action='append', type=int)
comments_parser_sl.add_argument('keyword', action='append')
comments_parser_sl.add_argument('source_id', type=int, required=True)
comments_parser_sl.add_argument('order', type=int, default=2)
comments_parser_sl.add_argument('label_sort_id', type=int)
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

document_parser = reqparse.RequestParser()
document_parser.add_argument('url', required=True)
document_parser.add_argument('title', required=True)
document_parser.add_argument('text', required=True)
document_parser.add_argument('timestamp', required=True)
document_parser.add_argument('metadata', default="")
document_parser.add_argument('source_id', required=True)
document_parser.add_argument('external_id', required=True)

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
comment_parser_post.add_argument('timestamp', required=True)
comment_parser_post.add_argument('external_id', required=True)


default_comment = '''
[{
	"source_id" : "999",
	"title": "...",
	"text": "...",
	"timestamp" : "2020-02-11T23:42:00+01:00",
	"external_id" : "42"
},
{
	"source_id" : "999",
	"title": "...",
	"text": "...",
	"timestamp" : "2020-02-11T23:42:00+01:00",
	"external_id" : "43"
}]
'''

comments_list_parser = reqparse.RequestParser()
comments_list_parser.add_argument('comments', type=str, default=default_comment, location='json')