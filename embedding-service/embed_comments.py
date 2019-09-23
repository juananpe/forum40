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
parser.add_argument('--keep-CLS', dest='keep_cls', default=True, action='store_true',
                    help='Include CLS when calculating embeddings for all the tokens (default: True).')
parser.add_argument('--use-tokens', dest='use_token', default=True, action='store_true',
                    help='Use tokens or CLS (default: True).')
parser.add_argument('--layers', dest='use_layers', type=int, default=4, nargs='?',
                    help='How many final model layers to use (default=4).')

args = parser.parse_args()


def process_batch(comment_batch):

    comment_texts = [concat(c[1], c[2]) for c in comment_batch]
    comment_embeddings = be.extract_features(comment_texts)

    batch_update_comments = []
    for i, comment_embedding in enumerate(comment_embeddings):
        # get comment object id
        comment_id = comment_batch[i][0]

        # update mongo db
        batch_update_comments.append(
            (comment_id, comment_embedding)
        )

    #import pdb
    #pdb.set_trace()

    cur.executemany(insert_statement, batch_update_comments)


# Connect to DB
conn = psycopg2.connect(host = args.host, port = args.port, dbname="omp", user="postgres", password="postgres")

insert_statement = """INSERT INTO embeddings (id, embedding) VALUES (%s, %s)"""

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

    # default: embed all comments
    embed_query = """SELECT c.id, c.title, c.text FROM comments c"""
    n_to_embed = n_comments

    if not embed_all:
        # select unembedded comments
        logger.info("Embedding unembedded comments only.")
        embed_query += " LEFT JOIN embeddings e ON c.id = e.id WHERE e.embedding IS NULL"

        cur.execute("""SELECT COUNT(*) FROM comments c LEFT JOIN embeddings e ON c.id = e.id WHERE e.embedding IS NULL""")
        n_to_embed = cur.fetchone()[0]
    else:
        # recreate table
        logger.info("Recreating embeddings table.")
        cur.execute("""DROP TABLE IF EXISTS public.embeddings""")
        cur.execute(
            """CREATE TABLE public.embeddings (
            id bigint NOT NULL,
            embedding float8[] NOT NULL);"""
        )
        conn.commit()

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
            # break

    # ensure primary key for embeddings
    if embed_all:
        cur.execute("""ALTER TABLE public.embeddings ADD CONSTRAINT embeddings_pk PRIMARY KEY (id)""")
        conn.commit()

except Exception as err:
    logger.error(err)
    traceback.print_tb(err.__traceback__)
finally:
    cur.close()
    # cursor_large.close()
    conn.close()
