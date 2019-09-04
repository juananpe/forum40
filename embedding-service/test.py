import pymongo, math
import nmslib, pickle
import sys
from utils import concat
import sklearn.metrics as sm
import numpy as np

client = pymongo.MongoClient("localhost", 27017)
db = client.omp

print("Loading index ...")
index = nmslib.init()
index.loadIndex("model/comment_vectors.index", load_data=True)
comment_id_mapping = pickle.load(open("model/comment_vectors.mapping", "rb"))
id_comment_mapping = {v: k for k, v in comment_id_mapping.items()}
print("Index loaded. \nWaiting for input of an id:")

comments = db.Comments
embeddings = db.Embeddings
print("-----------")

for sample_id in sys.stdin:
    print("-------------------")
    query_id = id_comment_mapping[int(sample_id.strip())]
    query_comment = comments.find_one({"_id": query_id})
    comment_text = concat(query_comment["title"], query_comment["text"])
    print("\n\n" + comment_text)
    print("-------------------")
    query_embedding = embeddings.find_one({"_id": query_id})
    ids, distances = index.knnQuery(query_embedding["embedding"], k=10)
    for i, id in enumerate(ids):

        print(str(id) + " " + str(distances[i]))
        sim_comment = comments.find_one({"_id": id_comment_mapping[id]})
        sim_embedding = embeddings.find_one({"_id": id_comment_mapping[id]})
        print(sim_comment["_id"])
        print(concat(sim_comment["title"], sim_comment["text"]))
        cos = sm.pairwise.cosine_similarity(np.array([query_embedding["embedding"], sim_embedding["embedding"]]))
        print("sklearn-cos:")
        print(cos)
