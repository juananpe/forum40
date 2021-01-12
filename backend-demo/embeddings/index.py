import traceback

import click
import hnswlib
import math
import numpy as np
import os
import requests

from apis.utils.tasks import ForumProcessor
from config.settings import EMBEDDING_INDEX_PATH

debug = False
max_batches = 100


class CommentIndexer(ForumProcessor):

    def __init__(self, source_id):
        super().__init__("indexing")

        # index
        self.source_id = source_id
        self.index_filename = os.path.join(EMBEDDING_INDEX_PATH, "hnsw_" + str(source_id) + ".index")
        self.index = hnswlib.Index(space='cosine', dim=768)

        # create empty index, if not existing
        if not os.path.isfile(self.index_filename):
            self.index.init_index(max_elements=300, ef_construction=300, M=48)
            self.index.save_index(self.index_filename)

        # config
        self.batch_size = 256

    def process(self):
        batch_i = 0
        cursor_large = None

        try:

            # get total size of the problem
            self.cursor.execute('SELECT count(*) FROM comments WHERE source_id = %s AND embedding IS NOT NULL', (self.source_id,))
            n_comments = self.cursor.fetchone()[0]
            n_batches = math.ceil(n_comments / self.batch_size)

            # incremental indexing: load index, set max comments to new value
            self.index.load_index(self.index_filename, max_elements=n_comments)
            self.index.set_ef(300)

            # cursor without withholding, since we do not commit any db updates
            cursor_large = self.conn.cursor(name='large_embedding', withhold=True)
            cursor_large.execute('SELECT id FROM comments WHERE source_id = %s AND embedding IS NOT NULL', (self.source_id,))

            new_embeddings_added = False

            while True:

                # keep track of progress
                batch_i += 1
                processed_comments = batch_i * self.batch_size
                self.logger.info(f"Batch {batch_i} of {n_batches} (comments: {processed_comments})")
                self.set_state({'step': 'add', 'progress': {'total': n_batches, 'current': batch_i}})

                # get batch from db
                records = cursor_large.fetchmany(size=self.batch_size)

                # stop if there are no more rows
                if not records:
                    break

                # collect db data
                comment_ids = [id[0] for id in records]

                # check if already indexed
                new_ids = []
                try:
                    # if one id is missing, an exception is thrown
                    _ = self.index.get_items(comment_ids)
                except:
                    # check one by one for missing ids
                    for i, comment_id in enumerate(comment_ids):
                        try:
                            _ = self.index.get_items([comment_id])
                        except RuntimeError:
                            new_ids.append(comment_id)

                if new_ids:
                    # get embeddings from db
                    self.cursor.execute('SELECT id, embedding FROM comments WHERE id IN %s', (tuple(new_ids),))
                    result_with_embeddings = self.cursor.fetchall()
                    new_tuples = [(row[0], row[1]) for row in result_with_embeddings]
                    new_ids, new_embeddings = zip(*new_tuples)

                    # add batch to index
                    self.logger.info(f"Adding {len(new_embeddings):d} embeddings to the index")
                    self.index.add_items(np.array(new_embeddings), new_ids)

                    new_embeddings_added = True

                # early stopping for debugging
                if debug and batch_i == max_batches:
                    break

        except Exception as err:
            self.logger.error(err)
            traceback.print_tb(err.__traceback__)

        finally:
            if cursor_large:
                cursor_large.close()

        # create and save index
        if new_embeddings_added:
            self.set_state({'step': 'save'})
            self.index.save_index(self.index_filename)
            message = f"Indexing finished and saved to {self.index_filename}"
            self.logger.info(message)
        else:
            self.logger.info("There are no new embeddings to index.")


@click.command(help='Index comment embeddings')
@click.argument('source-id', required=True, type=int)
def index(source_id: int):
    # start indexing
    indexer = CommentIndexer(source_id)
    indexer.start()

    # try to reload the index in the web app
    try:
        url = "http://localhost:5050/similarity/embeddings/reload-index/" + str(source_id)
        response = requests.get(url)
        if response.ok:
            print(response.json())
        else:
            print(f"Index not reloaded via api call {url}")
            print(response.reason)
    except:
        print("Error: Something went wrong during index reloading ...")
