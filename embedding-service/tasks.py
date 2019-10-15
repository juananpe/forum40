from app import huey

from index_comments import CommentIndexer
from embed_comments import CommentEmbedder

from BertFeatureExtractor import BertFeatureExtractor
from retrieve_comments import RetrieveComment

import os

# pg config
pg_host = os.getenv('PG_HOST', 'postgres')
pg_port = os.getenv('PG_PORT', 5432)

# load BERT model
print('Loading BERT model')
be = BertFeatureExtractor(
    batch_size=8,
    device='cpu',
    keep_cls=False,
    use_layers=4,
    use_token=True
)
print('BERT model loaded')


# db connection
try:
    retriever = RetrieveComment(pg_host, pg_port)
except:
    print('DB connection failed.')


@huey.task()
@huey.lock_task('indexing-lock')
def index_comments(db_host = "postgres", db_port = 5432):

    # start indexing
    indexer = CommentIndexer(db_host, db_port)
    indexer.indexEmbeddings()

    return True


@huey.task()
@huey.lock_task('embedding-lock')
def embed_comments():

    ce = CommentEmbedder(embed_all=False, batch_size=8, host=pg_host, port=pg_port)
    ce.setExtractorModel(be)

    # start embedding
    ce.embedComments()

    return True