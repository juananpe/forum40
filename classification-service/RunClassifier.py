import pymongo, argparse, pprint, logging
from collections import Counter
import numpy as np
from timeit import default_timer as timer
from pymongo import UpdateOne
from classifier import *
import pandas as pd
import time
import os
from sklearn.metrics import cohen_kappa_score



logger = logging.getLogger('Run Classifier logger')
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


class RunClassifier:
	def __init__(self, labelname, host = "mongo", port = 27017, cross_val=False):
        # db connection
		self.client = pymongo.MongoClient(host, port, w=0)
		self.db = self.client.omp_backup
		self.labels = self.db.Labels
		self.comments =self.db.Comments
		self.labelname = labelname
		self.label_id = None
		self.classification_model= None
		self.model=None
		self.batch_size =200
		self.cross_val=cross_val



	def collect_trainingdata(self):

		label = self.labels.find_one({"classname" : self.labelname})
		self.label_id = label["_id"]

		logger.info("Labelname: " + self.labelname + " (" + str(self.label_id) + ")")

		#join operation

		
		try:
			labeled_comments = self.comments.find(
		        {"labels" : {"$elemMatch" : {"manualLabels" : {"$ne" : None}, "labelId" :self.label_id}}})
		    		    
		except :
		    logging.error("No comments for label " + labelname)
		    exit(1)

		logger.info("Number of comments " + str(labeled_comments.count()))

		start = timer()
		# training data compilation
		annotation_dataset = []
		annotation_counts = Counter()
		for labeled_comment in labeled_comments:
				for current_label in labeled_comment["labels"]:
					if current_label["labelId"] == label["_id"]:
						if "manualLabels" in current_label:
							manual_label = current_label["manualLabels"][0]['label']
							annotation_counts[manual_label] += 1
							try:
								labeled_instance = (labeled_comment["embedding"],manual_label)
								#print(labeled_instance)
								annotation_dataset.append(labeled_instance)
							except KeyError:
								pass

		end = timer()

		logger.info("Manual annotations found: " + str(annotation_counts))
		logger.info("Length of datset: " + str(len(annotation_dataset)))
		logger.info("Dataset collection duration (seconds): " + str(end - start))

		return(annotation_dataset)

	def run_trainer(self,classifier=None):
		annotation_dataset = self.collect_trainingdata()
		# train model on embeddings
		self.classification_model = EmbedClassifier()

		if(self.cross_val):
			logger.info("Cross_validation started")
			start=timer()
			accuracy,f1_score,fit_time,score_time=self.classification_model.cross_validation(annotation_dataset, self.labelname,classifier)
			end=timer()
			logger.info("Cross validation took "+str(end-start)+" seconds.")
			return accuracy,f1_score,fit_time,score_time,len(annotation_dataset)
		else:
			self.classification_model = EmbedClassifier()
			logger.info("Training started")
			start=timer()
			self.model=self.classification_model.train(annotation_dataset, self.labelname)
			end=timer()
			logger.info("Training took "+str(end-start)+" seconds.")
			print(self.model)
			return len(annotation_dataset)



if __name__== "__main__":
    # argument parsing
	parser = argparse.ArgumentParser(description='Training Classifier.')
	parser.add_argument('--labelname', type=str, nargs='?', default='offtopic',
	                    help='name of the category to update')
	parser.add_argument('host', type=str, default='localhost', nargs='?',
	                    help='MongoDB host')
	parser.add_argument('port', type=int, default=27017, nargs='?',
	                    help='MongoDB port')
	args = parser.parse_args()
	labelname = args.labelname

	classifierRun = RunClassifier(labelname, host=args.host, port=args.port)
	
	classifier= LogisticRegression(
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
    
	classifierRun.run_trainer(classifier)
	

