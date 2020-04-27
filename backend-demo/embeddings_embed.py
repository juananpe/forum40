import argparse
import traceback
import math

from apis.utils.tasks import ForumProcessor, concat
from apis.utils.tasks import get_embeddings

class CommentEmbedder(ForumProcessor):

    def __init__(self, embed_all=False, batch_size=8, host="postgres", port=5432):
        super().__init__("embedding", host=host, port=port)
        self.cursor_large = None
        self.embed_all = embed_all
        self.batch_size = batch_size
        self.batch_i  = 0
        self.n_batches = 0
        self.n_commit = 100

    def set_commit_number(self, n_commit):
        self.n_commit = n_commit


    def process_batch(self, comment_batch):
        comment_texts = [concat(c[1], c[2]) for c in comment_batch if c[1] or c[2]]
        comment_ids = [c[0] for c in comment_batch if c[1] or c[2]]
        comment_embeddings, success = get_embeddings(comment_texts)
        if not success:
            self.logger.error("No embeddings retrieved from embedding-service")
            return False
        else:
            batch_update_comments = []
            for i, comment_embedding in enumerate(comment_embeddings):
                # get comment object id
                comment_id = comment_ids[i]

                # update mongo db
                batch_update_comments.append(
                    (comment_embedding, comment_id)
                )

            # write to db
            self.cursor.executemany("""UPDATE comments SET embedding=%s WHERE id=%s""", batch_update_comments)
            return True

    def init_cursor(self):
        try:

            self.cursor.execute("""SELECT COUNT(*) from comments""")
            n_comments = self.cursor.fetchone()[0]

            self.logger.info("Comments in the database: " + str(n_comments))

            embed_query = """SELECT id, title, text FROM comments"""
            self.n_to_embed = n_comments

            if not self.embed_all:
                embed_query += " WHERE embedding IS NULL"
                self.cursor.execute("""SELECT COUNT(*) from comments WHERE embedding IS NULL""")
                self.n_to_embed = self.cursor.fetchone()[0]

            self.logger.info("Comments to embed: " + str(self.n_to_embed))
            self.batch_i = 0
            self.n_batches = math.ceil(self.n_to_embed / self.batch_size)
            self.set_total(self.n_batches)

            self.cursor_large = self.conn.cursor(name='fetch_embeddings', withhold=True)
            self.cursor_large.execute(embed_query)

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
            message = "Batch: " + str(self.batch_i) + " of " + str(self.n_batches)
            self.logger.info(message)
            if self.batch_i % 10 == 0:
                self.update_state(self.batch_i, message)
        
        self.logger.info("Final commit to DB ...")
        self.conn.commit()
        self.close_cursor()


if __name__ == '__main__':
    # CLI parser
    parser = argparse.ArgumentParser(description='Embed comments in DB.')
    parser.add_argument('host', type=str, default='localhost', nargs='?',
                        help='DB host (default: localhost)')
    parser.add_argument('port', type=int, default=5432, nargs='?',
                        help='DB port (default: 5432)')
    parser.add_argument('source_id', type=int, default=1, nargs='?', 
                        help='Source id of the comment (default 1)')                        

    parser.add_argument('--embed-all', dest='all', default=False, action='store_true',
                        help='(Re-)embed all data (default: False)')
    parser.add_argument('--device', type=str, default='cpu', nargs='?',
                        help='Pytorch device for tensor operations (default: cpu, else cuda)')
    parser.add_argument('--batch-size', dest='batch_size', type=int, default=8, nargs='?',
                        help='Batch size for tensor operations (default: 8).')
    parser.add_argument('--include-CLS', dest='keep_cls', default=False, action='store_true',
                        help='Include CLS when calculating embeddings for all the tokens (default: True).')
    parser.add_argument('--exclude-tokens', dest='use_token', default=True, action='store_false',
                        help='Use tokens or CLS (default: True).')
    parser.add_argument('--layers', dest='use_layers', type=int, default=4, nargs='?',
                        help='How many final model layers to use (default=4).')

    args = parser.parse_args()

    # not really needed, right?
    source_id = args.source_id

    ce = CommentEmbedder(embed_all=args.all, batch_size=args.batch_size, host=args.host, port=args.port)

    # start embedding
    ce.process()


