import pymongo, math, argparse
from BertFeatureExtractor import BertFeatureExtractor

from app import concat

def process_batch(comment_ids):
    comment_batch = []
    for comment_id in comment_ids:
        comment_batch.append(comments.find_one({"_id": comment_id}))

    comment_texts = [concat(c["title"], c["text"]) for c in comment_batch]
    embeddings = be.extract_features(comment_texts)
    for i, comment in enumerate(embeddings):

        # get comment object id
        comment_id = comment_batch[i]["_id"]

        # get embedding
        comment_embedding = comment["embedding"]

        # update mongo db
        comments.update_one({"_id": comment_id}, {"$set": {'embedding':comment_embedding}}, upsert=False)

# CLI parser
parser = argparse.ArgumentParser(description='Embed comments in MongoDB.')
parser.add_argument('host', type=str, default='localhost', nargs='?',
                    help='MongoDB host')
parser.add_argument('port', type=int, default=27017, nargs='?',
                    help='MongoDB port')
parser.add_argument('--embed-all', dest='all', type=bool, default=False, nargs=1,
                    help='(Re-)embed all data (default False)')
args = parser.parse_args()


client = pymongo.MongoClient(args.host, args.port)
db = client.omp

print("Loading BERT model")
be = BertFeatureExtractor(batch_size=256)

comments = db.Comments

embed_all = args.all

comment_batch = []
batch_size = 32
batch_i = 0
i = 0
n_comments = comments.count()
n_batches = math.ceil(n_comments / batch_size)

# get all ids
ids_to_embed = []
if not embed_all:
    # only embed comments where no embedding is present
    for comment in comments.find({"embedding" : {"$exists" : False}}):
        ids_to_embed.append(comment["_id"])
else:
    # run embedding for all comments
    for comment in comments.find():
        ids_to_embed.append(comment["_id"])

print("Non-embedded comments:" + str(len(ids_to_embed)))

for comment_id in ids_to_embed:
    comment_batch.append(comment_id)
    i += 1
    if i % batch_size == 0:
        batch_i += 1
        print("Batch " + str(batch_i) + " of " + str(n_batches))

        process_batch(comment_batch)
        comment_batch = []

if comment_batch:
    process_batch(comment_batch)
