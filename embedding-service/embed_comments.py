import argparse, logging
from BertFeatureExtractor import BertFeatureExtractor
import utils
import psycopg2
import traceback
import sys

# create logger
logger = logging.getLogger('Embedding logger')
logger.setLevel(logging.INFO)

# create console handler and set level to info
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

update_statement = """UPDATE comments SET embedding=%s WHERE id=%s"""

class CommentEmbedder:

    def __init__(self, embed_all=False, batch_size=8, host="postgres", port=5432):
        # Connect to DB
        self.conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=utils.DB_NAME,
            user=utils.DB_USER,
            password=utils.DB_PASSWORD)
        self.cur = None
        self.embed_all = embed_all
        self.batch_size = batch_size
        self.logger = logger

    def __del__(self):
        self.conn.close()

    def setLogger(self, logger):
        self.logger = logger

    def setExtractorModel(self, model):
        self.be = model

    def process_batch(self, comment_batch):
        comment_texts = [utils.concat(c[1], c[2]) for c in comment_batch if c[1] or c[2]]
        comment_ids = [c[0] for c in comment_batch if c[1] or c[2]]
        comment_embeddings = self.be.extract_features(comment_texts)

        batch_update_comments = []
        for i, comment_embedding in enumerate(comment_embeddings):
            # get comment object id
            comment_id = comment_ids[i]

            # update mongo db
            batch_update_comments.append(
                (comment_embedding, comment_id)
            )

        self.logger.info("Start DB update")
        self.cur.executemany(update_statement, batch_update_comments)
        self.logger.info("DB updated")

    def embedComments(self):

        try:
            self.cur = self.conn.cursor()

            self.cur.execute("""SELECT COUNT(*) from comments""")
            n_comments = self.cur.fetchone()[0]

            self.logger.info("Comments in the database: " + str(n_comments))

            embed_query = """SELECT id, title, text FROM comments"""
            n_to_embed = n_comments

            if not self.embed_all:
                embed_query += " WHERE embedding IS NULL"
                self.cur.execute("""SELECT COUNT(*) from comments WHERE embedding IS NULL""")
                n_to_embed = self.cur.fetchone()[0]

            self.logger.info("Comments to embed: " + str(n_to_embed))

            batch_i = 0

            cursor_large = self.conn.cursor(name='fetch_large_result', withhold=True)
            cursor_large.execute(embed_query)

            while True:
                records = cursor_large.fetchmany(size=self.batch_size)

                if not records:
                    break

                batch_i += 1
                self.logger.info("Batch: " + str(batch_i) + "; comment " + str(batch_i * self.batch_size) + " of " + str(n_to_embed))

                self.process_batch(records)

                if batch_i % 100 == 0:
                    self.logger.info("Commit to DB ...")
                    self.conn.commit()

        except Exception as err:
            self.logger.error(err)
            traceback.print_tb(err.__traceback__)

        finally:
            self.cur.close()
            cursor_large.close()


if __name__ == '__main__':
    # CLI parser
    parser = argparse.ArgumentParser(description='Embed comments in DB.')
    parser.add_argument('host', type=str, default='localhost', nargs='?',
                        help='DB host (default: localhost)')
    parser.add_argument('port', type=int, default=5432, nargs='?',
                        help='DB port (default: 5432)')
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

    logger.info(args)

    print("Loading BERT model")
    be = BertFeatureExtractor(
        batch_size=args.batch_size,
        device=args.device,
        keep_cls=args.keep_cls,
        use_layers=args.use_layers,
        use_token=args.use_token
    )

    ce = CommentEmbedder(embed_all=args.all, batch_size=args.batch_size, host=args.host, port=args.port)
    ce.setExtractorModel(be)

    # start embedding
    ce.embedComments()


