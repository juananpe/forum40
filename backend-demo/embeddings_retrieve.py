import pprint
import nmslib
import argparse
from apis.utils.tasks import ForumTask, concat
from config.settings import EMBEDDING_INDEX_PATH

class RetrieveComment(ForumTask):

    def __init__(self, host="localhost", port=5432):
        super().__init__("retrieving", host=host, port=port)
        self.index = nmslib.init()
        self.comment_id_mapping = {}
        self.id_comment_mapping = {}
        self.load_index()

    def load_index(self):
        try:
            self.logger.info("Loading index")
            self.index.loadIndex(EMBEDDING_INDEX_PATH, load_data=False)
            self.logger.info("Loaded index with %d entries" % len(self.index))
        except:
            self.logger.error("No index of embeddings found in %s" % EMBEDDING_INDEX_PATH)

    def get_embedding(self, id):
        if type(id) != int:
            id = int(id)
        self.cursor.execute("""SELECT embedding FROM comments WHERE id = %s""", (id,))
        embedding = self.cursor.fetchone()[0]
        return embedding

    def get_nearest_for_id(self, id, n = 10, include_distance = False):
        if type(id) != int:
            id = int(id)
        query_embedding = self.get_embedding(id)
        ids, distances = self.index.knnQuery(query_embedding, k = (n + 1))
        if include_distance:
            return ids.tolist(), distances.tolist()
        else:
            return ids.tolist()

    def get_nearest_for_embedding(self, embedding, n = 10, include_distance = False):
        ids, distances = self.index.knnQuery(embedding, k = (n + 1))
        if include_distance:
            return ids.tolist(), distances.tolist()
        else:
            return ids.tolist()

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
    parser.add_argument('--n', type=int, default=10, nargs='?',
                        help='Nunmber of nearest neighbors (default: 10)')
    parser.add_argument('id', type=int, nargs='?', default=0, help='Id of the comment')
    args = parser.parse_args()
    positional_id = args.id

    if positional_id < 1:
        parser.error("Error: no valid positional id has been provided.")

    retriever = RetrieveComment(args.host, args.port)
    comment_id = positional_id
    embeddings = retriever.get_embedding(comment_id)

    retriever.logger.info("Length of the embedding: " + str(len(embeddings)))
    nn_ids = retriever.get_nearest_for_id(comment_id, args.n)

    retriever.logger.info("Selected sentence: " + retriever.get_comment_text(comment_id))
    retriever.logger.info("Nearest neighbour ids for " + str(comment_id))
    pprint.pprint(nn_ids)
    pprint.pprint([retriever.get_comment_text(id) for id in nn_ids])
