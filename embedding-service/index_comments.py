import pymongo, math
import nmslib, pickle
from app import concat

client = pymongo.MongoClient("localhost", 27017)
db = client.omp

index = nmslib.init(method='hnsw', space="angulardist", data_type=nmslib.DataType.DENSE_VECTOR)

comments = db.Comments

comments_query = {"embedding" : {"$exists" : True}}
# comments_query = {}

comment_batch = []
batch_size = 1024
batch_i = 0
i = 0
n_comments = comments.find(comments_query).count()
n_batches = math.ceil(n_comments / batch_size)

# get all ids
comment_id_mapping = {}
batch_embeddings = []

# from collections import defaultdict
# all_texts = defaultdict(int)

for comment_i, comment in enumerate(comments.find(comments_query)):
#    comment_text = concat(comment["title"], comment["text"])
#    all_texts[comment_text] += 1
#    if all_texts[comment_text] > 1:
#        print(str(comment["_id"]) + "   " + str(comment_i) + "    " + comment_text + "\n")
    comment_id_mapping[comment["_id"]] = comment_i
    batch_embeddings.append(comment["embedding"])
    if comment_i % batch_size == 0:
        print("Adding comment %d of %d" % (comment_i, n_comments))
        # index.addDataPointBatch(batch_embeddings)
        # batch_embeddings = []

if batch_embeddings:
    index.addDataPointBatch(batch_embeddings)

# create index
index.createIndex({'post': 2}, print_progress=True)

# save index
index.saveIndex("model/comment_vectors.index", save_data=True)
pickle.dump(comment_id_mapping, open("model/comment_vectors.mapping", "wb"))
