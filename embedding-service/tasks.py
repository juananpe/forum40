from celery import Celery
from celery.contrib.abortable import AbortableTask

from BertFeatureExtractor import BertFeatureExtractor

from index_comments import CommentIndexer
from embed_comments import CommentEmbedder

import pdb
import os, logging

logger = logging.getLogger()

# celery config
config_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
config_broker = "amqp://guest:guest@%s:5672//" % config_host

celery_app = Celery(
    'embedding_tasks',
    backend='rpc',
    broker=config_broker
)
celery_app.conf.update(
    timezone='Europe/Berlin',
    enable_utc=True,
    broker_heartbeat=0
)

# pg config
pg_host = os.getenv('PG_HOST', 'postgres')
pg_port = os.getenv('PG_PORT', 5432)


logger.info('Loading BERT model')
be = BertFeatureExtractor(
    batch_size=8,
    device='cpu',
    keep_cls=False,
    use_layers=4,
    use_token=True
)
logger.info('BERT model loaded')


def get_embeddings(sequences):
    return be.extract_features(sequences)


@celery_app.task(bind=True, ignore_result=True)
def index_comments(self, db_host = "postgres", db_port = 5432):

    # start indexing
    indexer = CommentIndexer(db_host, db_port)
    indexer.indexEmbeddings()

    return True


@celery_app.task(bind=True, base=AbortableTask, ignore_result=True)
def embed_comments(self):

    ce = CommentEmbedder(embed_all=False, batch_size=8, host=pg_host, port=pg_port)
    ce.setExtractorModel(be)
    ce.setLogger(logger)
    ce.initCursor()

    logger.info("Iteration over n batches: " + str(ce.n_batches))

    # run embedding
    while not self.is_aborted():
        logger.info("Processing batch %d of %d" % (ce.batch_i, ce.n_batches))
        ce.embedBatch()
        self.update_state(state='PROGRESS', meta={'done': ce.batch_i, 'total': ce.n_batches})

    # terminate gracefully
    ce.closeCursor()
    logger.warning('Embedding task stopped.')
    return True