import pprint
import hnswlib
import os
import argparse
from apis.utils.tasks import ForumTask, concat
from config.settings import EMBEDDING_INDEX_PATH

class RetrieveComment(ForumTask):

    def __init__(self, host="localhost", port=5432):
        super().__init__("retrieving", host=host, port=port)
        self.index = None
        self.comment_id_mapping = {}
        self.id_comment_mapping = {}
        self.loaded_index_source_id = None
 
    def load_index(self, source_id, force_reload = False):

        # only load index, if it not has been loaded before
        if not force_reload and self.loaded_index_source_id == source_id:
            return True

        try:
            self.index = hnswlib.Index(space = 'cosine', dim = 768)
            self.index_filename = os.path.join(EMBEDDING_INDEX_PATH, "hnsw_" + str(source_id) + ".index")
            self.logger.info("Loading index %s" % self.index_filename)
            self.index.load_index(self.index_filename)
            # set ef 300 from construction time
            self.index.set_ef(300)
            self.logger.info("Loaded index with %d entries" % self.index.get_current_count())
            self.loaded_index_source_id = source_id
            return True
        except:
            self.logger.error("No index of embeddings found in %s" % self.index_filename)
            return False


    def exist_in_index(id_list):
        # check if already indexed
        try:
            # if one id is missing, an exception is thrown
            _ = self.index.get_items(id_list)
            return []
        except:
            # check one by one for missing ids
            new_ids = []                   
            for i, comment_id in enumerate(id_list):
                try:
                    _ = self.index.get_items([comment_id])
                except RuntimeError:
                    new_ids.append(comment_id)
            return new_ids
    

    def add_to_index(id_list, embedding_list):
        pass

    def save_index():
        pass


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
        ids, distances = self.index.knn_query(query_embedding, k = (n + 1))
        if include_distance:
            return ids[0].tolist(), distances[0].tolist()
        else:
            return ids[0].tolist()

    def get_nearest_for_embedding(self, embedding, n = 10, include_distance = False):
        ids, distances = self.index.knn_query(embedding, k = (n + 1))
        if include_distance:
            return ids[0].tolist(), distances[0].tolist()
        else:
            return ids[0].tolist()

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
    parser.add_argument('source_id', type=int, nargs='?', default=1, help='Source id of the comment (default: 1)')                        
    parser.add_argument('id', type=int, nargs='?', default=0, help='Id of the comment')
    args = parser.parse_args()
    comment_id = args.id
    source_id = args.source_id

    if comment_id < 1:
        parser.error("Error: no valid positional id has been provided.")

    if source_id < 1:
        parser.error("Error: no valid positional id has been provided.")

    retriever = RetrieveComment(args.host, args.port)
    retriever.load_index(source_id)
    
    embeddings = retriever.get_embedding(comment_id)

    if not embeddings:
        print("Error: no embedding for id %d in database" % comment_id)
        exit(1)

    retriever.logger.info("Length of the embedding: " + str(len(embeddings)))
    nn_ids = retriever.get_nearest_for_id(comment_id, args.n)

    retriever.logger.info("Selected sentence: " + retriever.get_comment_text(comment_id))
    retriever.logger.info("Nearest neighbour ids for " + str(comment_id))
    pprint.pprint(nn_ids)
    for id in nn_ids:
        print(id, retriever.get_comment_text(id))
