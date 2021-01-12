from collections import Counter
from timeit import default_timer as timer

import click
from datetime import datetime
from typing import Dict

from apis.utils.tasks import ForumProcessor
from classification.classifier import EmbeddingClassifier, get_history_path


class ClassifierTrainer(ForumProcessor):
    def __init__(self, labelname, annotation_dataset=None, optimize=False, cv=True, classifier=None):
        super().__init__("classification_train")
        self.labelname = labelname
        self.label_id = None
        self.annotation_dataset = annotation_dataset
        self.optimize = optimize
        self.cv = cv
        if classifier:
            self.classifier = EmbeddingClassifier(classifier)
        else:
            self.classifier = EmbeddingClassifier()

    def get_trainingdata(self):
        start = timer()

        # get label id
        self.cursor = self.conn.cursor()
        self.cursor.execute('SELECT id FROM labels WHERE name = %s', (self.labelname,))
        self.label_id = self.cursor.fetchone()[0]
        if self.label_id is None:
            self.logger.error(f"Label {self.labelname} not found")
            exit(1)
        else:
            self.logger.info("Build classifier model for label: " + self.labelname + " (" + str(self.label_id) + ")")

        # count annotations
        self.cursor.execute(
            'SELECT count(*) FROM comments c JOIN annotations a ON c.id = a.comment_id WHERE a.label_id = %s',
            (self.label_id,))
        n_annotations = self.cursor.fetchone()[0]

        if not n_annotations:
            self.logger.info("No comments for training found.")
            exit(0)
        else:
            self.logger.info(f"Found {n_annotations:d} comments for training.")

        # select annotations
        self.cursor.execute(
            'SELECT c.id, c.embedding, a.label, a.user_id FROM comments c JOIN annotations a ON c.id = a.comment_id WHERE a.label_id = %s',
            (self.label_id,))

        # training data compilation
        annotation_dataset = []
        annotation_counts = Counter()
        annotations = self.cursor.fetchall()
        for annotation in annotations:
            comment_id = annotation[0]
            embedding = annotation[1]
            # skip multiple labels per comment
            if comment_id in annotation_counts:
                continue
            # skip empty embeddings
            if embedding:
                annotation_counts[comment_id] += 1
                annotation_dataset.append((annotation[1], annotation[2]))

        end = timer()

        self.logger.info("Length of dataset: " + str(len(annotation_dataset)))
        self.logger.info("Dataset collection duration (seconds): " + str(end - start))

        if not annotation_dataset:
            self.logger.info("No comments with embedding for training.")
            exit(0)

        return annotation_dataset

    def set_state(self, data: Dict):
        super().set_state(data | {'label_id': self.label_id})

    def process(self):
        annotation_dataset = self.get_trainingdata()

        # find best C parameter
        if self.optimize:
            self.logger.info("Hyperparameter optimzation started")
            start = timer()
            params = [0.01, 0.05, 0.1, 0.5, 1, 5, 10]
            best_C = 0
            best_F1 = 0
            best_acc = 0
            for param_num, C in enumerate(params):
                self.logger.info(f"Testing C = {C:.3f}")
                self.set_state({
                    'step': 'hyperparam',
                    'progress': {'total': len(params), 'current': param_num},
                    'params': {'C': C}
                })
                self.classifier.set_c(C)
                accuracy, f1_score, fit_time, score_time = self.classifier.cross_validation(
                    annotation_dataset
                )
                if f1_score > best_F1:
                    best_F1 = f1_score
                    best_acc = accuracy
                    best_C = C
            self.logger.info(f"Optimal C = {best_C:.3f}")
            self.logger.info(f"Performance: accuracy = {best_acc:.3f}, F1 = {best_F1:.3f}")
            # set best C parameter
            self.classifier.set_c(C)
            end = timer()
            self.logger.info(f"Hyperparameter optimzation finished after {str(end - start)} seconds.")

        # train final model
        self.set_state({'step': 'train'})
        self.logger.info("Training started")
        start = timer()
        self.model = self.classifier.train(annotation_dataset, self.labelname)
        end = timer()
        self.logger.info("Training finished after " + str(end - start) + " seconds.")

        # evaluate model
        if self.cv:
            self.logger.info("Cross-validating performance.")
            self.set_state({'step': 'cv'})
            acc, f1, fit_time, _ = self.classifier.cross_validation(annotation_dataset, k=10)
            with open(get_history_path(self.labelname), 'a', encoding="UTF-8") as f:
                # append history file
                result_string = ";".join([
                    datetime.today().isoformat(),  # timestamp
                    "training",  # task
                    self.labelname,  # label
                    str(len(annotation_dataset)),  # training set size
                    f"{acc:.3f}",  # cv acc
                    f"{f1:.3f}",  # cv f1
                    "0",  # stability score
                    f"{fit_time:.1f}",  # duration
                ])
                f.write(result_string + "\n")
                self.logger.info(result_string)

        return {
            'number_training_samples': len(annotation_dataset),
            'acc': acc,
            'f1': f1,
            'fit_time': fit_time
        }


@click.command(help='Classifier trainer')
@click.argument('source-id', required=True, type=int)
@click.option('--labelname', required=True, help='Name of the category for model training')
@click.option('--optimize', is_flag=True, help='Run C parameter optimization')
@click.option('--cv', is_flag=True, help='Perform cross validation after training')
def train(source_id: int, labelname: str, optimize: bool, cv: bool):
    classifier_trainer = ClassifierTrainer(labelname, optimize=optimize, cv=cv)
    classifier_trainer.start()
