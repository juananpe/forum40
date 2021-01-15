from timeit import default_timer as timer

import itertools
import math
import time
from datetime import datetime
from io import StringIO
from sklearn.metrics import cohen_kappa_score
from typing import Dict

from apis.service.colibert_client import CoLiBertClient
from core.tasks import ForumProcessor
from classification.classifier import EmbeddingClassifier, get_history_path
from classification.train import ClassifierTrainer


class LabelUpdater(ForumProcessor):
    """Functions for collection of training data and prediction on the entire DB"""

    def __init__(self, source_id, labelname, skip_confidence=False):
        super().__init__("classification_update")
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
        self.cursor.execute('SELECT id FROM labels WHERE name = %s', (self.labelname,))
        self.label_id = self.cursor.fetchone()[0]

    def init_cursor(self):
        """
        Initializes cursor that later (in process_batch) retreives all comments
        if skip_train is true, only select new comments that have not been labeled yet
        """

        self.cursor.execute(
            'SELECT count(*) FROM comments c WHERE c.source_id = %s',
            (self.source_id,)
        )
        self.n_facts = self.cursor.fetchone()[0]

        self.logger.info("Preparing cursor for updates ...")

        # init cursor for machine labels from facts table

        self.cursor_large = self.conn.cursor(name='fetch_facts_' + self.labelname, withhold=True)
        self.cursor_large.execute(
            'SELECT c.id, f.label, f.confidence '
            'FROM comments c '
            'JOIN facts f ON c.id = f.comment_id '
            'WHERE c.source_id = %s AND f.label_id = %s',
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
        self.cursor.execute(
            'INSERT INTO facts ( '
            '  SELECT c.id, %s, false, 0, 0 ' 
            '  FROM comments c ' 
            '  LEFT JOIN ( '
            '    SELECT * FROM facts WHERE label_id = %s ' 
            '  ) AS f ON c.id = f.comment_id ' 
            '  WHERE c.source_id = %s AND f.comment_id IS NULL '
            ')',
            (self.label_id, self.label_id, self.source_id),
        )

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
        self.cursor.execute('SELECT embedding FROM comments WHERE id IN %s', (batch_ids,))
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

    def process(self):
        start = timer()

        # load model
        try:
            self.classifier = EmbeddingClassifier()
            self.classifier.load_from_disk(self.labelname)
        except:
            raise Exception(
                f"Could not load classifier model for label {self.labelname}. "
                f"Run train.py first to create a model"
            )

        # make sure there is a fact entry for this label for every comment of a source
        self.init_facts()

        # init the large cursor which iterates over all comments of a source
        self.init_cursor()

        # keep track of progress with the SingleProcessManager
        n_total = math.ceil(self.n_facts / self.batch_size)

        # process comments batch by batch
        while self.process_batch():
            self.logger.info(f"Completed batch {self.batch_i} of {n_total}.")
            self.set_state({'progress': {'total': n_total, 'current': self.batch_i}})

        # close the large cursor
        self.close_cursor()

        # copy postgres
        self.buffer.seek(0)
        self.cursor.execute(
            'CREATE TEMP TABLE tmp_facts ('
            '  comment_id int8 NOT NULL, '
            '  label_id int8 NOT NULL, '
            '  label bool NULL DEFAULT false, '
            '  confidence float8 NULL DEFAULT 0, '
            '  CONSTRAINT tmp_facts_pk PRIMARY KEY (comment_id, label_id)'
            ')'
        )
        self.cursor.copy_from(self.buffer, 'tmp_facts')
        self.cursor.execute(
            'UPDATE facts f '
            'SET label = t.label, confidence = t.confidence '
            'FROM tmp_facts t '
            'WHERE f.comment_id = t.comment_id AND f.label_id=t.label_id'
        )
        self.cursor.execute('COMMIT; TRUNCATE TABLE tmp_facts;')
        self.cursor.execute('VACUUM FULL ANALYZE facts;')
        self.cursor.execute('REFRESH MATERIALIZED VIEW comments_time_summary;')

        # stability
        kappa_score = cohen_kappa_score(self.labels_old, self.labels_new)
        self.stability = kappa_score
        self.logger.info(f"Stability: {kappa_score:.3f}")

        # Commit updates
        self.logger.info("Commit to DB ...")
        self.conn.commit()

        # some useful information and status tracking
        end = timer()
        duration = end - start
        self.logger.info(f"{self.n_facts:d} label updates finished after {duration:.3f} seconds.")

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

    def set_state(self, data: Dict):
        super().set_state(data | {'label_id': self.label_id})

    def init_model_table(self):
        self.cursor.execute(
            'INSERT INTO model (label_id, timestamp) VALUES (%s, CURRENT_TIMESTAMP) RETURNING id',
            (self.label_id),
        )
        self.model_entry_id = self.cursor.fetchone()[0]
        self.logger.info(f"Init Model Entry: {self.label_id=}")

    def update_model_table(self, model_details):
        label_id = self.label_id
        number_training_samples = model_details['number_training_samples']
        acc = model_details['acc']
        f1 = model_details['f1']
        fit_time = model_details['fit_time']

        self.cursor.execute(
            'UPDATE model '
            'SET timestamp = CURRENT_TIMESTAMP, number_training_samples = %s, acc = %s, f1 = %s, fit_time = %s '
            'WHERE id = %s;',
            (number_training_samples, acc, f1, int(fit_time), self.model_entry_id),
        )
        self.logger.info(f"Update Model Entry: label_id={label_id}, number_training_samples={number_training_samples}")

    def update_colibert_labels(self):
        self.logger.info(f'Update sample comments with CoLiBERT scores')
        start = time.time()

        # get label description
        self.cursor.execute('SELECT description FROM labels WHERE id = %s', (self.label_id,))
        description = self.cursor.fetchone()[0]

        if not description:
            return

        # select sample comments
        self.cursor.execute('SELECT id, text FROM comments WHERE source_id = %s ORDER BY RANDOM() LIMIT %s', (self.source_id, 100))
        comments = self.cursor.fetchall()
        comment_ids, comment_texts = zip(*comments)

        # get CoLiBERT outputs
        score_matrix = CoLiBertClient().score_all_pairs(contexts=[description], queries=comment_texts)
        scores = [s[0] for s in score_matrix]

        # update scores in DB
        records = list(zip(scores, comment_ids, itertools.repeat(self.label_id)))
        self.cursor.executemany('UPDATE facts SET confidence = %s WHERE comment_id = %s and label_id = %s', records)
        self.conn.commit()

        end = time.time()
        self.logger.info(f'CoLiBERT fact initialization finished. Took {end - start:.01f}s')


def update(source_id: int, labelname: str, skip_confidence: bool = False, optimize: bool = False, init_facts_only: bool = False, skip_train: bool = False):
    label_updater = LabelUpdater(source_id, labelname, skip_confidence=skip_confidence)

    if init_facts_only:
        # just init all predictions with 0 (necessary, when new labels are inserted)
        label_updater.init_facts(commit_now=True)

        # Classify with CoLiBERT
        label_updater.update_colibert_labels()
    else:
        # init model entry
        label_updater.init_model_table()

        if not skip_train:
            # train model
            classifier_trainer = ClassifierTrainer(labelname, optimize=optimize, cv=True)
            model_details = classifier_trainer.start()

            # update model entry
            label_updater.update_model_table(model_details)

        # update predictions
        label_updater.start()
