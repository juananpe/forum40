import pymongo, argparse, pprint, logging
from collections import Counter
import numpy as np
from timeit import default_timer as timer
from pymongo import UpdateOne
from classifier import *
import pandas as pd
import time
import os
# create logger
logger = logging.getLogger('Measuring stability logger')
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

class StabilityMeasure:
    """Functions for collection of training data and prediction on entire MngoDB"""
    def __init__(self, labelname, host = "mongo", port = 27017):
        # db connection
        self.client = pymongo.MongoClient(host, port, w=0)
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

    

    def storeCrossValidation(self,classifier):

        # get training data from MongDB
        annotation_dataset = self.collect_trainingdata()

        # train model on embeddings
        self.classification_model = EmbedClassifier()
        logger.info("Cross_validation started")
        start=timer()
        mean_f1=self.classification_model.cross_validation(annotation_dataset, self.labelname,classifier)
        end=timer()
        logger.info("Cross validation took "+str(end-start)+" seconds.")

        model_name = type(classifier).__name__
        current_timestamp = time.time()

        if(os.path.isfile('history.csv')):
            df=pd.read_csv('history.csv')
            df = df.append({'model_name' :model_name,'model_parameters':classifier, 
                                        'time_stamp' :current_timestamp,'label_name':self.labelname,'cross_val_score':mean_f1 } , ignore_index=True)
            df.to_csv('models/history.csv')

        else:
            df = pd.DataFrame(columns=['model_name', 'model_parameters', 
                                                        'time_stamp','label_name','cross_val_score'])
            df = df.append({'model_name' :model_name,'model_parameters':classifier, 
                                        'time_stamp' :current_timestamp,'label_name':self.labelname,'cross_val_score':mean_f1 } , ignore_index=True)
            df.to_csv('history.csv')



        


if __name__== "__main__":
    # argument parsing
    parser = argparse.ArgumentParser(description='Measure cross validation.')
    parser.add_argument('--labelname', type=str, nargs='?', default='offtopic',
                        help='name of the category to cross val')
    parser.add_argument('host', type=str, default='localhost', nargs='?',
                        help='MongoDB host')
    parser.add_argument('port', type=int, default=27017, nargs='?',
                        help='MongoDB port')
    args = parser.parse_args()
    labelname = args.labelname

    classifier = LogisticRegression(
                            n_jobs=10, 
                            random_state=42,
                            class_weight='balanced',
                            solver='saga',
                            penalty= 'elasticnet',
                            tol=0.001,
                            max_iter=200,
                            C=1.0,
                            l1_ratio=0.1
                            
                        )
        
    stability_keeper = StabilityMeasure(labelname,host=args.host, port=args.port)
    stability_keeper.storeCrossValidation(classifier)

