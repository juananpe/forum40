import argparse, logging, psycopg2, math
import numpy as np
import utils
from timeit import default_timer as timer
from classifier import EmbeddingClassifier
from sklearn.metrics import cohen_kappa_score

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
        self.labels_old = None
        self.labels_new = None
        self.labelname = labelname
        self.batch_size = 10000
        self.batch_i = 0
        self.stability = 0
        try:
            self.classifier = EmbeddingClassifier()
            self.classifier.load_from_disk(labelname)
        except:
            logger.error(
                "Could not load classifier model for label %s. Run train.py first to create a model" % labelname)
            exit(1)

    def __del__(self):
        try:
            self.close_cursor()
        finally:
            self.conn.close()

    def init_cursor(self):

        # get number of facts
        facts_count = """SELECT count(*) FROM comments"""
        self.cur.execute(facts_count)
        self.n_facts = self.cur.fetchone()[0]

        # init cursor for machine labels from facts table
        facts_query = """SELECT c.id, c.embedding, f.label, f.confidence FROM comments c JOIN facts f ON c.id = f.comment_id WHERE f.label_id = %s"""
        self.cursor_large = self.conn.cursor(name='fetch_facts', withhold=True)
        self.cursor_large.execute(
            facts_query,
            (self.label_id,))

        # init label arrays for stability measure
        self.labels_old = []
        self.labels_new = []

    def close_cursor(self):
        if self.cur:
            self.cur.close()
        if self.cursor_large:
            self.cursor_large.close()

    def init_facts(self):

        # get label id
        self.cur = self.conn.cursor()
        self.cur.execute("""SELECT id FROM labels WHERE name=%s""", (self.labelname,))
        self.label_id = self.cur.fetchone()[0]
        logger.info("Predict new labels for: " + self.labelname + " (" + str(self.label_id) + ")")

        # init facts entry for all
        logger.info("Ensuring a fact entry for each comment for label %s" % (self.labelname,))
        facts_query = """INSERT INTO facts (SELECT c.id, %s, false, 0, 0 FROM comments c LEFT JOIN (SELECT * FROM facts WHERE label_id = %s) AS f ON c.id = f.comment_id WHERE f.comment_id IS NULL)"""
        self.cur.execute(
            facts_query,
            (self.label_id, self.label_id))

        # Commit updates
        logger.info("Commit to DB ...")
        self.conn.commit()


    def process_batch(self, update_confidence = True):

        # get records
        comment_batch = self.cursor_large.fetchmany(size=self.batch_size)

        if not comment_batch:
            # end of cursor
            return False

        self.batch_i += 1

        # remove comments without embedding
        comment_batch = [comment for comment in comment_batch if comment[1] is not None]

        if not comment_batch:
            # no embeddings in current batch. Go to next one
            return True

        # predict new labels
        ids, embeddings, labels_old, confidences = zip(*comment_batch)
        labels_new, confidences = self.classifier.predict(embeddings)

        # append stability measure
        for i, label in enumerate(labels_old):
            if label is not None:
                self.labels_old.append(label)
                self.labels_new.append(labels_new[i])

        # create bulk update
        if update_confidence:
            batch_update_facts = []
            for i, comment_id in enumerate(ids):
                bool_label = True if labels_new[i] == 1 else False
                batch_update_facts.append((bool_label, confidences[i], comment_id, self.label_id))

        # run bulk update
        if batch_update_facts:
            self.cur.executemany("""UPDATE facts SET label=%s, confidence=%s WHERE comment_id=%s AND label_id=%s""", batch_update_facts)

        return True


    def updateLabels(self):

        start = timer()

        self.init_facts()

        self.init_cursor()

        n_total = math.ceil(self.n_facts / self.batch_size)
        while self.process_batch():
            logger.info("Completed batch %d of %d." % (self.batch_i, n_total))

        self.close_cursor()

        # stability
        kappa_score = cohen_kappa_score(self.labels_old, self.labels_new)
        self.stability = kappa_score
        logger.info("Stability: %.3f" % (kappa_score,))

        # Commit updates
        logger.info("Commit to DB ...")
        self.conn.commit()

        end = timer()
        logger.info("%d label updates finished after %.3f seconds." % (self.n_facts, end - start))


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
