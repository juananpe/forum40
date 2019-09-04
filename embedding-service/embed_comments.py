import pymongo, argparse, logging
from BertFeatureExtractor import BertFeatureExtractor
from pymongo import UpdateOne

from app import concat

# create logger
logger = logging.getLogger('Embedding logger')
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

def process_batch(comment_batch):
    comment_texts = [concat(c["title"], c["text"]) for c in comment_batch]
    comment_embeddings = be.extract_features(comment_texts)
    batch_update_embeddings = []
    batch_update_comments = []
    for i, comment_embedding in enumerate(comment_embeddings):

        # get comment object id
        comment_id = comment_batch[i]["_id"]

        # update mongo db
        batch_update_embeddings.append(UpdateOne({"_id": comment_id}, {"$set": {'embedding' : comment_embedding["embedding"]}}))
        batch_update_comments.append(UpdateOne({"_id": comment_id}, {"$set": {'embedded': True}}))
    embeddings.bulk_write(batch_update_embeddings)
    comments.bulk_write(batch_update_comments)


# CLI parser
parser = argparse.ArgumentParser(description='Embed comments in MongoDB.')
parser.add_argument('host', type=str, default='localhost', nargs='?',
                    help='MongoDB host (default: localhost)')
parser.add_argument('port', type=int, default=27017, nargs='?',
                    help='MongoDB port (default: 27017)')
parser.add_argument('--embed-all', dest='all', type=bool, default=False, nargs=1,
                    help='(Re-)embed all data (default: False)')
parser.add_argument('--device', type=str, default='cpu', nargs='?',
                    help='Pytorch device for tensor operations (default: cpu, else cuda)')
parser.add_argument('--batch-size', dest='batch_size', type=int, default=8, nargs='?',
                    help='Batch size for tensor operations (default: 8).')
args = parser.parse_args()

# Connect to DB
client = pymongo.MongoClient(args.host, args.port)
db = client.omp

print("Loading BERT model")
be = BertFeatureExtractor(batch_size=256, device=args.device)

comments = db.Comments
embeddings = db["Embeddings"]

embed_all = args.all

n_comments = comments.count()

logger.info("Comments in the database: " + str(n_comments))

if embed_all:
    embed_query = {}
else:
    embed_query = {"embedded": {"$ne": True}}

batch_size = args.batch_size
batch_i = 0
i = 0
comment_batch = []
for comment in comments.find(
        embed_query,
        {"_id" : 1, "title" : 1, "text" : 1},
        cursor_type=pymongo.CursorType.EXHAUST,
        snapshot=True
):
    if not comment['title'] and not comment['text']:
        continue
    i += 1
    comment_batch.append(comment)
    if i % batch_size == 0:
        batch_i += 1
        logger.info("Batch: " + str(batch_i) + ";  comments: " + str(i))
        # get embeddings
        process_batch(comment_batch)
        # reset batch
        comment_batch = []

if comment_batch:
    process_batch(comment_batch)

