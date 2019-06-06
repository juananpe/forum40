import pymongo, math
from BertFeatureExtractor import BertFeatureExtractor

from app import concat

def process_batch(comment_batch):

    comment_texts = [concat(c["title"], c["text"]) for c in comment_batch]
    embeddings = be.extract_features(comment_texts)
    for i, comment in enumerate(embeddings):

        # get comment object id
        comment_id = comment_batch[i]["_id"]

        # get embedding
        comment_embedding = comment["embedding"]

        # update mongo db
        comments.update_one({"_id": comment_id}, {"$set": {'embedding':comment_embedding}}, upsert=False)


client = pymongo.MongoClient("localhost", 27017)
db = client.omp

print("Loading BERT model")
be = BertFeatureExtractor(batch_size=256)

comments = db.Comments

comment_batch = []
batch_size = 256
batch_i = 0
i = 0
n_comments = comments.count()
n_batches = math.ceil(n_comments / batch_size)
for comment in comments.find():
    comment_batch.append(comment)
    i += 1
    if i % batch_size == 0:
        batch_i += 1
        print("Batch " + str(batch_i) + " of " + str(n_batches))

        process_batch(comment_batch)
        comment_batch = []

if comment_batch:
    process_batch(comment_batch)