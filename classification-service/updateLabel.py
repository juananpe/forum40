import pymongo, argparse, pprint, logging
from collections import Counter
import numpy as np
from timeit import default_timer as timer
from pymongo import UpdateOne
from classifier import *

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

class LabelUpdater:
    """Functions for collection of training data and prediction on entire MngoDB"""
    def __init__(self, labelname):
        # db connection
        self.client = pymongo.MongoClient("localhost", 27017, w=0)
        self.db = self.client.omp
        self.labels = self.db.Labels
        self.comments = self.db.Comments

        self.labelname = labelname
        self.label_id = None
        self.classification_model = None
        self.batch_size = 20000

    def collect_trainingdata(self):

        label = self.labels.find_one({"classname" : self.labelname})
        self.label_id = label["_id"]

        logger.info("Labelname: " + self.labelname + " (" + str(self.label_id) + ")")

        try:
            labeled_comments = self.comments.find(
                {"labels" : {"$elemMatch" : {"manualLabels" : {"$ne" : None}, "labelId" :self.label_id}}}
            )
        except:
            logging.error("No comments for label " + labelname)
            exit(1)

        logger.info("Number of comments " + str(labeled_comments.count()))

        start = timer()
        # training data compilation
        annotation_dataset = []
        annotation_counts = Counter()
        for labeled_comment in labeled_comments:

            if not "embedding" in labeled_comment:
                continue

            for current_label in labeled_comment["labels"]:
                if current_label["labelId"] == label["_id"]:
                    if "manualLabels" in current_label:
                        manual_label = current_label["manualLabels"][0]['label']
                        annotation_counts[manual_label] += 1
                        labeled_instance = (labeled_comment["embedding"],manual_label)
                        annotation_dataset.append(labeled_instance)
        end = timer()

        logger.info("Manual annotations found: " + str(annotation_counts))
        logger.info("Length of datset: " + str(len(annotation_dataset)))
        logger.info("Dataset collection duration (seconds): " + str(end - start))

        return(annotation_dataset)

    def process_batch(self, comment_batch):

        comments_object, embeddings = zip(*comment_batch)
        start=timer()
        comment_labels = self.classification_model.predict(embeddings, labelname)
        end =timer()
        logger.info("Batch took "+str((end-start))+" seconds of prediction time")

        start=timer()
        batch_updates = []
        for i, comment in enumerate(comments_object):

            comment_id = comment["_id"]
            confidence = comment_labels[i].tolist()

            # initialize labels field for comment
            if "labels" in comment:
                labels_object = {"labels" : comment["labels"]}
            else:
                labels_object = {"labels" : []}

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
        bulk_results=self.comments.bulk_write(batch_updates)

        end=timer()

        logger.info("Batch took "+str((end-start))+" seconds of writing time")

        # print output for debug
        # if "labels" in comment:
        #     # pprint.pprint(comment["labels"])
        #     pprint.pprint({"$set": labels_object})
        #     print("----------------")

        return bulk_results


    def updateLabels(self):

        # get training data from MongDB
        annotation_dataset = self.collect_trainingdata()

        # train model on embeddings
        self.classification_model = EmbedClassifier()
        logger.info("Training started")
        start=timer()
        self.classification_model.train(annotation_dataset, self.labelname)
        end=timer()
        logger.info("Training took "+str(end-start)+" seconds.")

        # db update
        comment_batch = []
        i = 0
        for comment in self.comments.find({},
                                          {'_id':1, 'embedding':1, 'labels':1},
                                          cursor_type=pymongo.CursorType.EXHAUST,
                                          snapshot=True):

            if not "embedding" in comment:
                continue

            comment_batch.append((comment, comment["embedding"]))
            i += 1

            if i % self.batch_size == 0:
                self.process_batch(comment_batch)
                comment_batch = []
                print("comments_processed "+str(i))
                # break

        # last batch
        if comment_batch:
            self.process_batch(comment_batch)


if __name__== "__main__":
    # argument parsing
    parser = argparse.ArgumentParser(description='Update category labels.')
    parser.add_argument('--labelname', type=str, nargs='?', default='offtopic',
                        help='name of the category to update')
    args = parser.parse_args()
    labelname = args.labelname

    labelUpdater = LabelUpdater(labelname)
    labelUpdater.updateLabels()

