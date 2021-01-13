import traceback

import math
from pypika import PostgreSQLQuery, Table, Parameter
from pypika.functions import Count

from apis.service.embedding_service_client import EmbeddingServiceClient
from core.tasks import ForumProcessor
from db.repositories.util import Random
from embeddings.utils import concat


class CommentEmbedder(ForumProcessor):
    def __init__(self, source_id: int, embed_all=False, batch_size=8):
        super().__init__("embedding")
        self.source_id = source_id
        self.cursor_large = None
        self.embed_all = embed_all
        self.batch_size = batch_size
        self.batch_i = 0
        self.n_batches = 0
        self.n_commit = 100

    def set_commit_number(self, n_commit):
        self.n_commit = n_commit

    def process_batch(self, comment_batch):
        comment_texts = [concat(c[1], c[2]) for c in comment_batch if c[1] or c[2]]
        comment_ids = [c[0] for c in comment_batch if c[1] or c[2]]
        comment_embeddings, success = EmbeddingServiceClient().embed(comment_texts)
        if not success:
            self.logger.error("No embeddings retrieved from embedding-service")
            return False
        else:
            batch_update_comments = []
            for i, comment_embedding in enumerate(comment_embeddings):
                comment_id = comment_ids[i]
                batch_update_comments.append((comment_embedding, comment_id))

            self.cursor.executemany('UPDATE comments SET embedding = %s WHERE id = %s', batch_update_comments)
            return True

    def init_cursor(self):
        try:
            comments = Table('comments')
            query = PostgreSQLQuery() \
                .from_(comments) \
                .where(comments.source_id == Parameter('%s'))

            if not self.embed_all:
                query = query.where(comments.embedding.notnull())

            self.cursor.execute(query.select(Count('*')).get_sql(), (self.source_id,))
            n_to_embed = self.cursor.fetchone()[0]

            self.batch_i = 0
            self.n_batches = math.ceil(n_to_embed / self.batch_size)

            embed_query = query.select(comments.id, comments.title, comments.text).orderby(Random())
            self.cursor_large = self.conn.cursor(name='fetch_embeddings', withhold=True)
            self.cursor_large.execute(embed_query.get_sql(), (self.source_id,))

        except Exception as err:
            self.logger.error(err)
            traceback.print_tb(err.__traceback__)

    def close_cursor(self):
        if self.cursor_large:
            self.cursor_large.close()

    def embed_batch(self):

        # increase batch counter
        self.batch_i += 1

        # get records
        records = self.cursor_large.fetchmany(size=self.batch_size)

        # stop if there are no more records
        if not records:
            return False

        # get embeddings
        success = self.process_batch(records)
        if not success:
            return False

        # commit every n batches
        if self.batch_i % self.n_commit == 0:
            self.logger.info("Commit to DB ...")
            self.conn.commit()

        return True

    def process(self):
        self.init_cursor()
        while self.embed_batch():
            self.logger.info(f"Batch {self.batch_i} of {self.n_batches}")
            if self.batch_i % 10 == 0:
                self.set_state({'progress': {'total': self.n_batches, 'current': self.batch_i}})

        self.logger.info("Final commit to DB ...")
        self.conn.commit()
        self.close_cursor()


def embed(source_id: int, embed_all: bool = False, batch_size: int = 8):
    ce = CommentEmbedder(source_id=source_id, embed_all=embed_all, batch_size=batch_size)
    ce.start()
