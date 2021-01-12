import click
import hnswlib
import os
import pprint

from apis.utils.tasks import ForumTask, concat
from config.settings import EMBEDDING_INDEX_PATH


class RetrieveComment(ForumTask):
    def __init__(self):
        super().__init__("retrieving")
        self.index = None
        self.comment_id_mapping = {}
        self.id_comment_mapping = {}
        self.loaded_index_source_id = None

    def load_index(self, source_id, force_reload=False):
        # only load index, if it not has been loaded before
        if not force_reload and self.loaded_index_source_id == source_id:
            return True

        self.index = hnswlib.Index(space='cosine', dim=768)
        index_filename = os.path.join(EMBEDDING_INDEX_PATH, "hnsw_" + str(source_id) + ".index")
        self.logger.info(f"Loading index {index_filename}")
        try:
            self.index.load_index(index_filename)
            # set ef 300 from construction time
            self.index.set_ef(300)
            self.logger.info(f"Loaded index with {self.index.get_current_count():d} entries")
            self.loaded_index_source_id = source_id
            return True
        except:
            self.logger.error(f"No index of embeddings found in {index_filename}")
            return False

    def get_embedding(self, id):
        if type(id) != int:
            id = int(id)
        self.cursor.execute('SELECT embedding FROM comments WHERE id = %s', (id,))
        embedding = self.cursor.fetchone()[0]
        return embedding

    def get_nearest_for_id(self, id, n=10, include_distance=False):
        if type(id) != int:
            id = int(id)
        query_embedding = self.get_embedding(id)
        ids, distances = self.index.knn_query(query_embedding, k=(n + 1))
        if include_distance:
            return ids[0].tolist(), distances[0].tolist()
        else:
            return ids[0].tolist()

    def get_nearest_for_embedding(self, embedding, n=10, include_distance=False):
        ids, distances = self.index.knn_query(embedding, k=(n + 1))
        if include_distance:
            return ids[0].tolist(), distances[0].tolist()
        else:
            return ids[0].tolist()

    def get_comment_text(self, id):
        if type(id) != int:
            id = int(id)
        self.cursor.execute('SELECT title, text FROM comments WHERE id = %s', (id,))
        comment = self.cursor.fetchone()
        return concat(comment[0], comment[1])


@click.command()
@click.argument('source-id', required=True, type=int)
@click.argument('comment-id', required=True, type=int)
@click.option('--n', default=10, help='Number of nearest neighbors')
def retrieve(source_id: int, comment_id: int, n: int):
    retriever = RetrieveComment()
    retriever.load_index(source_id)

    embeddings = retriever.get_embedding(comment_id)

    if not embeddings:
        print(f"Error: no embedding for id {comment_id} in database")
        exit(1)

    retriever.logger.info("Length of the embedding: " + str(len(embeddings)))
    nn_ids = retriever.get_nearest_for_id(comment_id, n)

    retriever.logger.info("Selected sentence: " + retriever.get_comment_text(comment_id))
    retriever.logger.info("Nearest neighbour ids for " + str(comment_id))
    pprint.pprint(nn_ids)
    for nn_comment_id in nn_ids:
        print(nn_comment_id, retriever.get_comment_text(nn_comment_id))
