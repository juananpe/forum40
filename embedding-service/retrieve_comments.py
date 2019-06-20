import pymongo, math
import nmslib, pickle
import sys

client = pymongo.MongoClient("localhost", 27017)
db = client.omp

print("Loading index ...")
index = nmslib.init(method='hnsw', space='cosinesimil')
index.loadIndex("model/comment_vectors.index", load_data=True)
comment_id_mapping = pickle.load(open("model/comment_vectors.mapping", "rb"))
id_comment_mapping = {v: k for k, v in comment_id_mapping.items()}
print("Index loaded. \nWaiting for input of an id:")


comments = db.Comments

for sample_id in sys.stdin:
    query_id = id_comment_mapping[int(sample_id.strip())]
    query_comment = comments.find_one({"_id": query_id})
    print("\n\n" + query_comment["text"])
    print("-------------------")
    ids, distances = index.knnQuery(query_comment["embedding"], k=10)
    for i, id in enumerate(ids):
        print(str(id) + " " + str(distances[i]))
        sim_comment = comments.find_one({"_id": id_comment_mapping[id]})
        print(sim_comment["_id"])
        print(sim_comment["text"])