from collections import Counter
from timeit import default_timer as timer

import argparse
from datetime import datetime

from apis.utils.tasks import ForumProcessor
from classification_classifier import EmbeddingClassifier, get_history_path


class ClassifierTrainer(ForumProcessor):
    def __init__(self, labelname, classifier=None, host="postgres", port=5432):
        super().__init__("classification", host=host, port=port)
        self.labelname = labelname
        self.label_id = None
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
        n_annotations = self.cursor.fetchone()

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

    def train(self, annotation_dataset=None, optimize=False, cv=True):
        if annotation_dataset is None:
            annotation_dataset = self.get_trainingdata()

        self.set_total(1)
        if cv:
            self.total_steps += 1
        step = 0

        # find best C parameter
        if optimize:
            self.logger.info("Hyperparameter optimzation started")
            start = timer()
            params = [0.01, 0.05, 0.1, 0.5, 1, 5, 10]
            best_C = 0
            best_F1 = 0
            best_acc = 0
            self.set_total(1 + len(params))
            for step, C in enumerate(params):
                message = f"Testing C = {C:.3f}"
                self.update_state(step + 1, message)
                self.logger.info(message)
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
        step += 1
        message = "Training started"
        self.update_state(step, message)
        self.logger.info(message)
        start = timer()
        self.model = self.classifier.train(annotation_dataset, self.labelname)
        end = timer()
        message = "Training finished after " + str(end - start) + " seconds."
        self.logger.info(message)
        self.update_state(step, message)

        # evaluate model
        if cv:
            step += 1
            message = "Cross-validating performance."
            self.logger.info(message)
            self.update_state(step, message)
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
                self.update_state(step, result_string)

        return {
            'number_training_samples': len(annotation_dataset),
            'acc': acc,
            'f1': f1,
            'fit_time': fit_time
        }


if __name__ == "__main__":
    # argument parsing
    parser = argparse.ArgumentParser(description='Classifier trainer.')
    parser.add_argument('--labelname', type=str, nargs='?', default='offtopic',
                        help='Name of the category for model training')
    parser.add_argument('--optimize', dest='optimize', default=False, action='store_true',
                        help='Run C parameter optimization (default: False)')
    parser.add_argument('--cv', dest='cv', default=False, action='store_true',
                        help='Perform cross validation after training (default: False)')
    parser.add_argument('source_id', type=1, default=1, nargs='?',
                        help='Source id (default: 1)')
    parser.add_argument('host', type=str, default='localhost', nargs='?',
                        help='DB host (default: localhost)')
    parser.add_argument('port', type=int, default=5432, nargs='?',
                        help='DB port (default: 5432)')
    args = parser.parse_args()
    labelname = args.labelname

    classifier_trainer = ClassifierTrainer(labelname, host=args.host, port=args.port)

    classifier_trainer.train(optimize=args.optimize, cv=args.cv)
