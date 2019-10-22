import argparse, logging, psycopg2
import utils

from collections import Counter
from timeit import default_timer as timer
from classifier import EmbeddingClassifier

# create logger
logger = logging.getLogger('Classifier logger')
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

class ClassifierTrainer:

    def __init__(self, labelname, classifier = None, host="postgres", port=5432):
        self.logger = logger
        # db connection
        self.conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=utils.DB_NAME,
            user=utils.DB_USER,
            password=utils.DB_PASSWORD)
        self.cur = None
        self.labelname = labelname
        self.label_id = None
        if classifier:
            self.classifier = EmbeddingClassifier(classifier)
        else:
            self.classifier = EmbeddingClassifier()

    def setLogger(self, logger):
        self.logger = logger

    def get_trainingdata(self):

        start = timer()

        # get label id
        self.cur = self.conn.cursor()
        self.cur.execute("""SELECT id FROM labels WHERE name=%s""", (self.labelname,))
        self.label_id = self.cur.fetchone()[0]
        if self.label_id is None:
            logging.error("Label %s not found" % self.labelname)
            exit(1)
        else:
            self.logger.info("Build classifier model for label: " + self.labelname + " (" + str(self.label_id) + ")")

        # count annotations
        self.cur.execute(
            """SELECT count(*) FROM comments c JOIN annotations a ON c.id=a.comment_id WHERE a.label_id=%s""",
            (self.label_id,))
        n_annotations = self.cur.fetchone()

        if not n_annotations:
            logging.info("No comments for training found.")
            exit(0)
        else:
            logging.info("Found %d comments for training." % n_annotations)

        # select annotations
        self.cur.execute(
            """SELECT c.id, c.embedding, a.label, a.user_id FROM comments c JOIN annotations a ON c.id=a.comment_id WHERE a.label_id=%s""",
            (self.label_id,))

        # training data compilation
        annotation_dataset = []
        annotation_counts = Counter()
        annotations = self.cur.fetchall()
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

        return annotation_dataset

    def train(self, annotation_dataset=None, optimize=False):
        if annotation_dataset is None:
            annotation_dataset = self.get_trainingdata()

        # import pdb
        # pdb.set_trace()

        # find best C parameter
        if (optimize):
            self.logger.info("Hyperparameter optimzation started")
            start = timer()
            params = [0.01, 0.05, 0.1, 0.5, 1, 5, 10]
            best_C = 0
            best_F1 = 0
            best_acc = 0
            for C in params:
                self.logger.info("Testing C = %.3f" % C)
                self.classifier.setC(C)
                accuracy, f1_score, fit_time, score_time = self.classifier.cross_validation(
                    annotation_dataset
                )
                if f1_score > best_F1:
                    best_F1 = f1_score
                    best_acc = accuracy
                    best_C = C
            self.logger.info("Optimal C = %.3f" % best_C)
            self.logger.info("Performance: accuracy = %.3f, F1 = %.3f" % (best_acc, best_F1))
            # set best C parameter
            self.classifier.setC(C)
            end = timer()
            self.logger.info("Hyperparameter optimzation finished after " + str(end - start) + " seconds.")

        # train final model
        self.logger.info("Training started")
        start = timer()
        self.model = self.classifier.train(annotation_dataset, self.labelname)
        end = timer()
        self.logger.info("Training finished after " + str(end - start) + " seconds.")



if __name__ == "__main__":
    # argument parsing
    parser = argparse.ArgumentParser(description='Classifier trainer.')
    parser.add_argument('--labelname', type=str, nargs='?', default='offtopic',
                        help='name of the category to update')
    parser.add_argument('--optimize', dest='optimize', default=False, action='store_true',
                        help='Run C parameter optimization (default: False)')
    parser.add_argument('host', type=str, default='localhost', nargs='?',
                        help='DB host')
    parser.add_argument('port', type=int, default=5432, nargs='?',
                        help='DB port')
    args = parser.parse_args()
    labelname = args.labelname

    classifierTrainer = ClassifierTrainer(labelname, host=args.host, port=args.port)

    print(classifierTrainer.train(optimize=args.optimize))
