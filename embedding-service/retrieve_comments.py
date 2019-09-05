import pymongo, pprint, logging
import nmslib, pickle
from utils import concat
import argparse
from bson import ObjectId

logger = logging.getLogger('Comments Retrieval Logger')
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


class RetrieveComment:

    def __init__(self, host="mongo", port=27017, nearest_neighbours=10):
        self.client = pymongo.MongoClient(host, port)
        self.db = self.client.omp
        self.comments = self.db.Comments
        logger.info("Loading Index")
        self.index = nmslib.init()
        self.index.loadIndex("model/comment_vectors.index", load_data=True)
        logger.info("Index Loaded")
        logger.info("Loading comment vectors")
        self.comment_id_mapping = pickle.load(open("model/comment_vectors.mapping", "rb"))
        logger.info("Comment vectors loaded")
        self.id_comment_mapping = {v: k for k, v in self.comment_id_mapping.items()}
        self.nearest_neighbours = nearest_neighbours

    def get_mongodb_id(self, p_id):
        return self.id_comment_mapping[p_id]

    def get_embedding(self, _id):
        if type(_id) == str:
            _id = ObjectId(_id)
        embedding = self.comments.find_one({"_id": _id})
        return embedding["embedding"]

    def get_nearest_ids(self, _id):
        if (type(_id) == str):
            _id = ObjectId(_id)

        query_comment = self.comments.find_one({"_id": _id})
        ids, distances = self.index.knnQuery(query_comment["embedding"], k=(self.nearest_neighbours + 1))
        comment_db_id = []
        for _id_ in ids:
            if (self.id_comment_mapping[_id_] != _id):
                comment_db_id.append(self.id_comment_mapping[_id_])
        return comment_db_id

    def get_nearest_embedding(self, embedding):
        ids, distances = self.index.knnQuery(embedding, k=(self.nearest_neighbours + 1))
        comment_db_id = []
        for _id_ in ids:
            comment_db_id.append(self.id_comment_mapping[_id_])
        return comment_db_id

    def get_comment_text(self, _id):
        if type(_id) == str:
            _id = ObjectId(_id)
        comment = self.comments.find_one({"_id" : _id})
        return concat(comment["title"], comment["text"])


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='comment retrieval')
    parser.add_argument('--host', type=str, default='localhost', nargs='?',
                        help='MongoDB host')
    parser.add_argument('--port', type=int, default=27017, nargs='?',
                        help='MongoDB port')
    parser.add_argument('pid', type=int, nargs='?', default=0, help='Positional id of the comment')
    args = parser.parse_args()
    positional_id = args.pid

    if positional_id < 1:
        parser.error("Error: no valid positional id has been provided.")

    retriever = RetrieveComment('localhost', 27017)
    comment_id = retriever.get_mongodb_id(positional_id)
    embeddings = retriever.get_embedding(comment_id)

    if (embeddings != -1):
        logger.info("Length of the embedding: " + str(len(embeddings)))
    nn_ids = retriever.get_nearest_ids(comment_id)
    if (nn_ids != -1):
        print(retriever.get_comment_text(comment_id))
        logger.info("Nearest neighbour ids for " + str(comment_id))
        pprint.pprint(nn_ids)
        pprint.pprint([retriever.get_comment_text(id) for id in nn_ids])
