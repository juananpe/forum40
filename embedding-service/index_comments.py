import pymongo, math
import nmslib, pickle

client = pymongo.MongoClient("localhost", 27017)

print(client)

db = client.omp

index = nmslib.init(method='hnsw', space="angulardist", data_type=nmslib.DataType.DENSE_VECTOR)

comments = db.Comments
embeddings = db.Embeddings

comment_batch = []
batch_size = 32
batch_i = 0
i = 0
n_comments = embeddings.find({}).count()
n_batches = math.ceil(n_comments / batch_size)

# get all ids
comment_id_mapping = {}
comment_id_running = 0
batch_embeddings = []
batch_ids = []

# index batches
for comment_i, comment in enumerate(embeddings.find({})):
    batch_ids.append(comment_id_running)
    comment_id_mapping[comment["_id"]] = comment_id_running
    comment_id_running += 1
    batch_embeddings.append(comment["embedding"])
    if comment_i > 0 and comment_i % batch_size == 0:
        print("Adding comment %d of %d" % (comment_i, n_comments))
        # import pdb
        # pdb.set_trace()
        index.addDataPointBatch(data = batch_embeddings, ids = batch_ids)
        batch_embeddings = []
        batch_ids = []

# ensure indexing of last batch
if batch_embeddings:
    index.addDataPointBatch(data = batch_embeddings, ids = batch_ids)

# create index
index.createIndex({'post': 2}, print_progress=True)

# save index
index.saveIndex("model/comment_vectors.index", save_data=True)
pickle.dump(comment_id_mapping, open("model/comment_vectors.mapping", "wb"))
