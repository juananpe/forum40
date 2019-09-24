import pprint, logging
import nmslib, pickle
from utils import concat
import argparse
import psycopg2

logger = logging.getLogger('Comments Retrieval')
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

    def __init__(self, host="localhost", port=5432, nearest_neighbours = 10):
        self.client = psycopg2.connect(host = args.host, port = args.port, dbname="omp", user="postgres", password="postgres")
        self.cursor = self.client.cursor()
        self.index = nmslib.init()
        self.comment_id_mapping = {}
        self.id_comment_mapping = {}
        self.nearest_neighbours = nearest_neighbours
        self.load_index()

    def load_index(self):
        try:
            logger.info("Loading index")
            self.index.loadIndex("model/comment_vectors.index", load_data=True)
            #logger.info("Loading comment vectors")
            #self.comment_id_mapping = pickle.load(open("model/comment_vectors.mapping", "rb"))
            ## reverse mapping
            #self.id_comment_mapping = {v: k for k, v in self.comment_id_mapping.items()}
        except:
            logger.error("No index of embeddings found in ./model directory.")


    def get_embedding(self, id):
        if type(id) != int:
            id = int(id)

        self.cursor.execute("""SELECT embedding FROM comments WHERE id = %s""", (id,))
        embedding = self.cursor.fetchone()[0]
        return embedding

    def get_nearest_ids(self, id):
        if type(id) != int:
            id = int(id)
        query_embedding = self.get_embedding(id)
        ids, distances = self.index.knnQuery(query_embedding, k = (self.nearest_neighbours + 1))
        #comment_db_id = []
        #for _id_ in ids:
        #    if (self.id_comment_mapping[_id_] != _id):
        #        comment_db_id.append(str(self.id_comment_mapping[_id_]))
        return ids

    def get_nearest_embedding(self, embedding):
        ids, distances = self.index.knnQuery(embedding, k = (self.nearest_neighbours + 1))
        embeddings = []
        for _id_ in ids:
            embeddings.append(self.index[_id_])
        return embeddings

    def get_comment_text(self, id):
        if type(id) != int:
            id = int(id)
        self.cursor.execute("""SELECT title, text FROM comments WHERE id = %s""", (id,))
        comment = self.cursor.fetchone()
        return concat(comment[0], comment[1])


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Nearest neighbor comment retrieval')
    parser.add_argument('--host', type=str, default='localhost', nargs='?',
                        help='DB host')
    parser.add_argument('--port', type=int, default=5432, nargs='?',
                        help='DB port')
    parser.add_argument('id', type=int, nargs='?', default=0, help='Id of the comment')
    args = parser.parse_args()
    positional_id = args.id

    if positional_id < 1:
        parser.error("Error: no valid positional id has been provided.")

    retriever = RetrieveComment(args.host, args.port)
    comment_id = positional_id
    embeddings = retriever.get_embedding(comment_id)


    logger.info("Length of the embedding: " + str(len(embeddings)))
    nn_ids = retriever.get_nearest_ids(comment_id)

    print(retriever.get_comment_text(comment_id))
    logger.info("Nearest neighbour ids for " + str(comment_id))
    pprint.pprint(nn_ids)
    pprint.pprint([retriever.get_comment_text(id) for id in nn_ids])
