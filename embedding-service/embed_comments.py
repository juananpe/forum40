import pymongo, argparse, logging
from BertFeatureExtractor import BertFeatureExtractor
from utils import concat
import psycopg2
import traceback

# create logger
logger = logging.getLogger('Embedding logger')
logger.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

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

def process_batch(comment_batch):

    comment_texts = [concat(c[1], c[2]) for c in comment_batch if c[1] or c[2]]
    comment_ids = [c[0] for c in comment_batch if c[1] or c[2]]
    comment_embeddings = be.extract_features(comment_texts)

    batch_update_comments = []
    for i, comment_embedding in enumerate(comment_embeddings):
        # get comment object id
        comment_id = comment_ids[i]

        # update mongo db
        batch_update_comments.append(
            (comment_embedding, comment_id)
        )

    cur.executemany(update_statement, batch_update_comments)


# Connect to DB
conn = psycopg2.connect(host = args.host, port = args.port, dbname="omp", user="postgres", password="postgres")

update_statement = """UPDATE comments SET embedding=%s WHERE id=%s"""

try:
    cur = conn.cursor()
    batch_size = args.batch_size

    print("Loading BERT model")
    be = BertFeatureExtractor(
        batch_size=batch_size,
        device=args.device,
        keep_cls=args.keep_cls,
        use_layers=args.use_layers,
        use_token=args.use_token
    )

    embed_all = args.all

    cur.execute("""SELECT COUNT(*) from comments""")
    n_comments = cur.fetchone()[0]

    logger.info("Comments in the database: " + str(n_comments))

    embed_query = """SELECT id, title, text FROM comments"""
    n_to_embed = n_comments

    if not embed_all:
        embed_query += " WHERE embedding IS NULL"
        cur.execute("""SELECT COUNT(*) from comments WHERE embedding IS NULL""")
        n_to_embed = cur.fetchone()

    logger.info("Comments to embed: " + str(n_to_embed))

    batch_i = 0

    cursor_large = conn.cursor(name='fetch_large_result', withhold=True)
    cursor_large.execute(embed_query)

    while True:
        records = cursor_large.fetchmany(size=batch_size)

        if not records:
            break

        batch_i += 1
        logger.info("Batch: " + str(batch_i) + ";  comment " + str(batch_i * batch_size) + " of " + str(n_to_embed))

        process_batch(records)

        if batch_i % 100 == 0:
            logger.info("Commit to DB ...")
            conn.commit()

except Exception as err:
    logger.error(err)
    traceback.print_tb(err.__traceback__)

finally:
    cur.close()
    # cursor_large.close()
    conn.close()
