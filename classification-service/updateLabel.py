import pymongo, argparse, pprint, logging
from collections import Counter
import numpy as np
from timeit import default_timer as timer
from pymongo import UpdateOne
from classifier import *
from RunClassifier import *
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

class LabelUpdater(RunClassifier):
    """Functions for collection of training data and prediction on entire MngoDB"""
    
    
    def process_batch(self, comment_batch):

        comments_object, embeddings = zip(*comment_batch)
        start=timer()
        comment_labels = self.classification_model.predict(embeddings, self.labelname,self.model,
            get_from_file=False)
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
        super().run_trainer()
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
                break

        # last batch
        if comment_batch:
            self.process_batch(comment_batch)


if __name__== "__main__":
    # argument parsing
    parser = argparse.ArgumentParser(description='Update category labels.')
    parser.add_argument('--labelname', type=str, nargs='?', default='offtopic',
                        help='name of the category to update')
    parser.add_argument('host', type=str, default='localhost', nargs='?',
                        help='MongoDB host')
    parser.add_argument('port', type=int, default=27017, nargs='?',
                        help='MongoDB port')
    args = parser.parse_args()
    labelname = args.labelname

    labelUpdater = LabelUpdater(labelname, host=args.host, port=args.port)
    labelUpdater.updateLabels()

