import pymongo, math
import nmslib, pickle
import psycopg2
import logging, traceback, argparse

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
args = parser.parse_args()

# Connect to DB
conn = psycopg2.connect(host = args.host, port = args.port, dbname="omp", user="postgres", password="postgres")

# init index
index = nmslib.init(method='hnsw', space="cosinesimil", data_type=nmslib.DataType.DENSE_VECTOR)

# config
batch_size = 256
debug = False
max_batches = 100

# batch and id vars
comment_id_mapping = {}
comment_id_running = 0
batch_embeddings = []
batch_ids = []
batch_i = 0

try:
    cursor_large = conn.cursor(name='fetch_large_result', withhold=True)
    cursor_large.execute("SELECT id, embedding FROM comments WHERE embedding IS NOT NULL")

    while True:
        records = cursor_large.fetchmany(size=batch_size)

        if not records:
            break

        batch_i += 1
        logger.info("Batch: " + str(batch_i) + ";  comment " + str(batch_i * batch_size))

        batch_embeddings = [r[1] for r in records]
        batch_ids = [r[0] for r in records]

        # add batch
        index.addDataPointBatch(data=batch_embeddings, ids=batch_ids)

        if debug and batch_i == max_batches:
            break


except Exception as err:
    logger.error(err)
    traceback.print_tb(err.__traceback__)

finally:
    cursor_large.close()
    # cursor_large.close()
    conn.close()



# create and save index
index.createIndex({'post': 2}, print_progress=True)
index.saveIndex("model/comment_vectors.index", save_data=True)
print()
logger.info("Index saved to ./model")
