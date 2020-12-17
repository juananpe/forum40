from timeit import default_timer as timer

import argparse
import itertools
import math
import time
from datetime import datetime
from io import StringIO
from sklearn.metrics import cohen_kappa_score

from apis.service.colibert_client import CoLiBertClient
from apis.utils.tasks import ForumProcessor
from classification_classifier import EmbeddingClassifier, get_history_path
from classification_train import ClassifierTrainer


class LabelUpdater(ForumProcessor):
    """Functions for collection of training data and prediction on the entire DB"""

    def __init__(self, source_id, labelname, host="postgres", port=5432, skip_confidence=False):
        super().__init__("classification", host=host, port=port)
        self.cursor_large = None
        self.labels_old = None
        self.labels_new = None
        self.source_id = source_id
        self.labelname = labelname
        self.skip_confidence = skip_confidence
        self.batch_size = 5000
        self.batch_i = 0
        self.stability = 0
        self.buffer = StringIO()

        # get label id
        self.cursor.execute("""SELECT id FROM labels WHERE name=%s""", (self.labelname,))
        self.label_id = self.cursor.fetchone()[0]

    def init_cursor(self, skip_train=False):
        """
        Initializes cursor that later (in process_batch) retreives all comments
        if skip_train is true, only select new comments that have not been labeled yet
        """

        # get number of facts
        if skip_train:
            facts_count = """SELECT count(*) FROM comments c JOIN facts f ON c.id = f.comment_id WHERE c.source_id = %s AND f.label_id = %s and f.confidence = 0"""
            facts_query = """SELECT c.id, f.label, f.confidence FROM comments c JOIN facts f ON c.id = f.comment_id WHERE c.source_id = %s AND f.label_id = %s and f.confidence = 0"""
        else:
            facts_count = """SELECT count(*) FROM comments c WHERE c.source_id = %s """
            facts_query = """SELECT c.id, f.label, f.confidence FROM comments c JOIN facts f ON c.id = f.comment_id WHERE c.source_id = %s AND f.label_id = %s"""

        self.cursor.execute(facts_count, (self.source_id,))
        self.n_facts = self.cursor.fetchone()[0]

        self.logger.info("Preparing cursor for updates ...")

        # init cursor for machine labels from facts table

        self.cursor_large = self.conn.cursor(name='fetch_facts_' + self.labelname, withhold=True)
        self.cursor_large.execute(
            facts_query,
            (self.source_id, self.label_id))

        # init label arrays for stability measure
        self.labels_old = []
        self.labels_new = []

    def close_cursor(self):
        if self.cursor_large:
            self.cursor_large.close()

    def init_facts(self, commit_now=False):
        self.logger.info("Predict new labels for: " + self.labelname + " (" + str(self.label_id) + ")")

        # init facts entry for all
        self.logger.info(f"Ensuring a fact entry for each comment for label {self.labelname}")
        facts_query = """INSERT INTO facts (SELECT c.id, %s, false, 0, 0 FROM comments c LEFT JOIN (SELECT * FROM facts WHERE label_id = %s) AS f ON c.id = f.comment_id WHERE c.source_id = %s AND f.comment_id IS NULL)"""
        self.cursor.execute(
            facts_query,
            (self.label_id, self.label_id, self.source_id))

        # for a full update, we do not need a commit here
        if commit_now:
            # Commit updates
            self.logger.info("Commit to DB ...")
            self.conn.commit()

    def process_batch(self):
        # get records
        comment_batch = self.cursor_large.fetchmany(size=self.batch_size)

        if not comment_batch:
            # end of cursor
            return False

        self.batch_i += 1

        # get embeddings
        batch_ids = tuple([comment[0] for comment in comment_batch])
        self.cursor.execute("""SELECT embedding FROM comments WHERE id IN %s""", (batch_ids,))
        # remove comments without embedding
        filtered_batch = []
        for i, embedding in enumerate(self.cursor.fetchall()):
            if embedding[0]:
                entry = comment_batch[i]
                entry = entry + embedding
                filtered_batch.append(entry)

        if not filtered_batch:
            # no embeddings in current batch. Go to next one
            return True

        # predict new labels
        ids, labels_old, confidences, embeddings = zip(*filtered_batch)
        labels_new, confidences = self.classifier.predict(embeddings)

        # append stability measure
        for i, label in enumerate(labels_old):
            if label is not None:
                self.labels_old.append(label)
                self.labels_new.append(labels_new[i])

        # create bulk update
        batch_update_facts = []
        for i, comment_id in enumerate(ids):
            bool_label = True if labels_new[i] == 1 else False
            if self.skip_confidence and bool_label == labels_old[i]:
                # skip update for unchanged label
                continue
            self.buffer.write(str(comment_id) + "\t" + str(self.label_id) + "\t" + str(bool_label) + "\t" + str(confidences[i]) + "\n")

        # look at next batch
        return True

    def updateLabels(self):
        start = timer()

        # load model
        try:
            self.classifier = EmbeddingClassifier()
            self.classifier.load_from_disk(labelname)
        except:
            self.logger.error(
                f"Could not load classifier model for label {labelname}. Run train.py first to create a model")
            exit(1)

        # make sure there is a fact entry for this label for every comment of a source
        self.init_facts()

        # init the large cursor which iterates over all comments of a source
        self.init_cursor()

        # keep track of progress with the SingleProcessManager
        n_total = math.ceil(self.n_facts / self.batch_size)
        self.set_total(n_total + 3)  # 3 additional steps: stability, commit, finished

        # process comments batch by batch
        while self.process_batch():
            message = f"Completed batch {self.batch_i} of {n_total}."
            self.logger.info(message)
            self.update_state(self.batch_i, message)

        # close the large cursor
        self.close_cursor()

        # copy postgres
        self.buffer.seek(0)
        self.cursor.execute("CREATE TEMP TABLE tmp_facts (comment_id int8 NOT NULL, label_id int8 NOT NULL, label bool NULL DEFAULT false, confidence float8 NULL DEFAULT 0, CONSTRAINT tmp_facts_pk PRIMARY KEY (comment_id, label_id));")
        self.cursor.copy_from(self.buffer, 'tmp_facts')
        self.cursor.execute("UPDATE facts f SET label=t.label, confidence=t.confidence FROM tmp_facts t WHERE f.comment_id=t.comment_id AND f.label_id=t.label_id;")
        self.cursor.execute("COMMIT; TRUNCATE TABLE tmp_facts;")
        self.cursor.execute("VACUUM FULL ANALYZE facts;")

        # stability
        kappa_score = cohen_kappa_score(self.labels_old, self.labels_new)
        self.stability = kappa_score
        message = f"Stability: {kappa_score:.3f}"
        self.logger.info(message)
        self.update_state(self.batch_i + 1, message)

        # Commit updates
        message = "Commit to DB ..."
        self.logger.info(message)
        self.update_state(self.batch_i + 2, message)
        self.conn.commit()

        # some useful information and status tracking
        end = timer()
        duration = end - start
        message = f"{self.n_facts:d} label updates finished after {duration:.3f} seconds."
        self.logger.info(message)
        self.update_state(self.batch_i + 3, message)

        # update history
        with open(get_history_path(self.labelname), 'a', encoding="UTF-8") as f:
            # append history file
            f.write(";".join([
                datetime.today().isoformat(),  # timestamp
                "update",  # task
                self.labelname,  # label
                str(self.n_facts),  # training set size
                "0",  # cv acc
                "0",  # cv f1
                f"{self.stability:.3f}",  # stability score
                f"{duration:.1f}",  # duration
            ]))

    def initModelTable(self):
        self.cursor.execute(" INSERT INTO model (label_id, timestamp, pid) VALUES(%s, CURRENT_TIMESTAMP, %s) RETURNING id;", (self.label_id, self.pid))
        self.model_entry_id = self.cursor.fetchone()[0]
        self.logger.info(f"Init Model Entry: label_id={self.label_id}, pid={self.pid}")

    def updateModelTable(self, model_details):
        label_id = self.label_id
        number_training_samples = model_details['number_training_samples']
        acc = model_details['acc']
        f1 = model_details['f1']
        fit_time = model_details['fit_time']

        self.cursor.execute("UPDATE model SET timestamp=CURRENT_TIMESTAMP, number_training_samples=%s, acc=%s, f1=%s, fit_time=%s, pid=%s WHERE id=%s;", (number_training_samples, acc, f1, int(fit_time), None, self.model_entry_id))
        self.logger.info(f"Update Model Entry: label_id={label_id}, number_training_samples={number_training_samples}")

    def updateColibertLabels(self):
        self.logger.info(f'Update sample comments with CoLiBERT scores')
        start = time.time()

        # get label description
        self.cursor.execute("SELECT description FROM labels WHERE id = %s", (self.label_id,))
        description = self.cursor.fetchone()[0]

        if not description:
            return

        # select sample comments
        self.cursor.execute("SELECT id, text FROM comments WHERE source_id = %s ORDER BY RANDOM() LIMIT %s", (self.source_id, 100))
        comments = self.cursor.fetchall()
        comment_ids, comment_texts = zip(*comments)

        # get CoLiBERT outputs
        score_matrix = CoLiBertClient().score_all_pairs(contexts=[description], queries=comment_texts)
        scores = [s[0] for s in score_matrix]

        # update scores in DB
        records = list(zip(scores, comment_ids, itertools.repeat(self.label_id)))
        self.cursor.executemany("UPDATE facts SET confidence = %s WHERE comment_id = %s and label_id = %s", records)
        self.conn.commit()

        end = time.time()
        self.logger.info(f'CoLiBERT fact initialization finished. Took {end - start:.01f}s')


if __name__ == "__main__":
    # argument parsing
    parser = argparse.ArgumentParser(description='Update category labels.')

    parser.add_argument('--labelname', type=str, nargs='?', default='offtopic',
                        help='Name of the category to update')
    parser.add_argument('--skip-confidence', dest='skip_confidence', default=False, action='store_true',
                        help='Update changing labels only (default: False)')
    parser.add_argument('--optimize', dest='optimize', default=False, action='store_true',
                        help='Perform hyperparameter optimization (default: False)')
    parser.add_argument('--init-facts-only', dest='init_facts', default=False, action='store_true',
                        help='Do not predict anything, but init the fact table for a label (default: False)')

    parser.add_argument('--skip-train', dest='skip_train', default=False, action='store_true',
                        help='Skip retraining model.')

    parser.add_argument('host', type=str, default='localhost', nargs='?',
                        help='DB host (default: localhost)')
    parser.add_argument('port', type=int, default=5432, nargs='?',
                        help='DB port (default: 5432)')
    parser.add_argument('source_id', type=int, default=1, nargs='?',
                        help='Source id (default: 1)')
    args = parser.parse_args()

    labelname = args.labelname
    source_id = args.source_id
    optimize = args.optimize

    classifierTrainer = ClassifierTrainer(labelname, host=args.host, port=args.port)
    labelUpdater = LabelUpdater(source_id, labelname, host=args.host, port=args.port, skip_confidence=args.skip_confidence)

    if args.init_facts:
        # just init all predictions with 0 (necessary, when new labels are inserted)
        labelUpdater.init_facts(commit_now=True)

        # Classify with CoLiBERT
        labelUpdater.updateColibertLabels()
    else:
        # init model entry
        labelUpdater.initModelTable()

        if not args.skip_train:
            # train model
            model_details = classifierTrainer.train(optimize=optimize, cv=True)

            # update model entry
            labelUpdater.updateModelTable(model_details)

        # update predictions
        labelUpdater.updateLabels()
