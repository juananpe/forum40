import argparse, logging, psycopg2
import numpy as np
import utils
from timeit import default_timer as timer
from classifier import EmbeddingClassifier

# create logger
logger = logging.getLogger('Classifier update logger')
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


class LabelUpdater:
    """Functions for collection of training data and prediction on the entire DB"""

    def __init__(self, labelname, host="postgres", port=5432):
        # db connection
        self.conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=utils.DB_NAME,
            user=utils.DB_USER,
            password=utils.DB_PASSWORD)
        self.cur = None
        self.cursor_large = None
        self.labelname = labelname
        self.current_labels = {}
        try:
            self.classifier = EmbeddingClassifier.load_from_disk(labelname)
        except:
            logger.error(
                "Could not load classifier model for label %s. Run train.py first to create a model" % labelname)
            exit(1)

    def __del__(self):
        try:
            self.closeCursor()
        finally:
            self.conn.close()

    def init_cursor(self):

        start = timer()

        # get label id
        self.cur = self.conn.cursor()
        self.cur.execute("""SELECT id FROM labels WHERE name=%s""", (self.labelname,))
        self.label_id = self.cur.fetchone()[0]
        logger.info("Predict new labels for: " + self.labelname + " (" + str(self.label_id) + ")")

        # get machine labels
        self.cursor_large = self.conn.cursor(name='fetch_large_result', withhold=True)
        self.cursor_large.execute(
            """SELECT c.id, c.embedding, f.label, f.confidence FROM comments c JOIN facts f ON c.id=f.comment_id WHERE f.label_id=%s""",
            (self.labelname,))

    def close_cursor(self):
        if self.cur:
            self.cur.close()
        if self.cursor_large:
            self.cursor_large.close()

    def process_batch(self, comment_batch):

        start = timer()

        # predict new labels
        ids, embeddings, labels, confidences = zip(*comment_batch)
        comment_labels = self.classifier.predict(embeddings)


        # append stability measure

        # create bulk update

        # run bulk update

        comments_object, embeddings = zip(*comment_batch)
        start = timer()

        end = timer()
        logger.info("Batch took " + str((end - start)) + " seconds of prediction time")

        start = timer()
        batch_updates = []
        for i, comment in enumerate(comments_object):

            comment_id = comment["_id"]
            confidence = comment_labels[i].tolist()

            # initialize labels field for comment
            if "labels" in comment:
                labels_object = {"labels": comment["labels"]}
            else:
                labels_object = {"labels": []}

            # manipulate machine classification entry
            target_label_object = None
            for current_label in labels_object["labels"]:
                if current_label["labelId"] == self.label_id:
                    target_label_object = current_label

            # initialize if not present
            if not target_label_object:
                target_label_object = {
                    "labelId": self.label_id
                }
                labels_object["labels"].append(target_label_object)

            # set results
            target_label_object["classified"] = int(np.argmax(confidence))
            target_label_object["confidence"] = confidence

            # append bulk update
            batch_updates.append(
                UpdateOne({"_id": comment_id}, {"$set": labels_object}, upsert=False))

        # update mongo db
        bulk_results = self.comments.bulk_write(batch_updates)

        end = timer()

        logger.info("Batch took " + str((end - start)) + " seconds of writing time")

        return bulk_results

    # TODO : include the option for hyperparmeterized model for each
    def updateLabels(self):

        # get training data from MongDB
        super().run_trainer()
        # db update
        comment_batch = []
        i = 0
        for comment in self.comments.find({},
                                          {'_id': 1, 'embedding': 1, 'labels': 1},
                                          cursor_type=pymongo.CursorType.EXHAUST,
                                          snapshot=True):

            if not "embedding" in comment:
                continue
            comment_batch.append((comment, comment["embedding"]))

            i += 1

            if i % self.batch_size == 0:
                self.process_batch(comment_batch)
                comment_batch = []
                print("comments_processed " + str(i))
                break

        # last batch
        if comment_batch:
            self.process_batch(comment_batch)


if __name__ == "__main__":
    # argument parsing
    parser = argparse.ArgumentParser(description='Update category labels.')
    parser.add_argument('--labelname', type=str, nargs='?', default='offtopic',
                        help='name of the category to update')
    parser.add_argument('host', type=str, default='localhost', nargs='?',
                        help='DB host')
    parser.add_argument('port', type=int, default=5432, nargs='?',
                        help='DB port')
    args = parser.parse_args()
    labelname = args.labelname

    labelUpdater = LabelUpdater(labelname, host=args.host, port=args.port)
    labelUpdater.updateLabels()
