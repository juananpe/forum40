import nmslib
import traceback, argparse
import math

from apis.utils.tasks import ForumProcessor

debug = False
max_batches = 100

class CommentIndexer(ForumProcessor):

    def __init__(self, host="postgres", port=5432):
        super().__init__("indexing", host = host, port = port)

        # index
        self.index = nmslib.init(method='hnsw', space="cosinesimil", data_type=nmslib.DataType.DENSE_VECTOR)

        # config
        self.batch_size = 256

    def process(self):

        batch_i = 0
        cursor_large = None

        try:

            # get total size of the problem
            self.cursor.execute("""SELECT count(*) FROM comments WHERE embedding IS NOT NULL""")
            n_comments = self.cursor.fetchone()[0]
            n_batches = math.ceil(n_comments / self.batch_size)
            # set twice as much because collection and indexing takes more or less the same amount of time
            self.set_total(n_batches * 2)

            cursor_large = self.conn.cursor(name='fetch_large_result', withhold=True)
            cursor_large.execute("SELECT id, embedding FROM comments WHERE embedding IS NOT NULL")

            while True:

                # get batch from db
                records = cursor_large.fetchmany(size=self.batch_size)

                # stop if there are no more rows
                if not records:
                    break

                # keep track of progress
                batch_i += 1
                processed_comments = batch_i * self.batch_size
                message = "Batch %d of %d (comments: %d)" % (batch_i, n_batches, processed_comments)
                self.logger.info(message)
                self.update_state(batch_i, message)

                # extract columns separately
                batch_embeddings = [r[1] for r in records]
                batch_ids = [r[0] for r in records]

                # add batch to index
                self.index.addDataPointBatch(data=batch_embeddings, ids=batch_ids)

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
        self.update_state(batch_i + 1, "Create index (this may take a while)")
        self.index.createIndex({'post': 2}, print_progress=True)
        self.index.saveIndex("model/comment_vectors.index", save_data=False)
        print()
        message = "Indexing finished and  saved to ./model"
        self.logger.info(message)
        # set progress to 100%
        self.update_state(batch_i * 2, message)


if __name__ == '__main__':
    # CLI parser
    parser = argparse.ArgumentParser(description='Embed comments in DB.')
    parser.add_argument('host', type=str, default='localhost', nargs='?',
                        help='DB host (default: localhost)')
    parser.add_argument('port', type=int, default=5432, nargs='?',
                        help='DB port (default: 5432)')
    args = parser.parse_args()

    # start indexing
    indexer = CommentIndexer(args.host, args.port)
    indexer.process()
