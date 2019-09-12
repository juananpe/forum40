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
from RunClassifier import *


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

class StabilityMeasure(RunClassifier):
     
    
    def getBatchPredict(self,comment_batch):
        

        comments_object, embeddings = zip(*comment_batch)
        start=timer()
        comment_labels = self.classification_model.predict(embeddings, self.labelname,self.model,
            get_from_file=False)
        end =timer()
        logger.info("Batch took "+str((end-start))+" seconds of prediction time")
        start=timer()
        current_predict=[]
        previous_predict=[]


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

            #do not append if the previous mahchine lable is not present
            if target_label_object:
                previous_predict.append(target_label_object["classified"])
                current_predict.append(int(np.argmax(confidence)))            
       
        return previous_predict,current_predict


    def getStability(self):
        # db update
        comment_batch = []
        i = 0
        previous_predict_all=[]
        current_predict_all=[]

        for comment in self.comments.find({},
                                          {'_id':1, 'embedding':1, 'labels':1},
                                          cursor_type=pymongo.CursorType.EXHAUST,
                                          snapshot=True):

            i += 1
            if not "embedding" in comment:
                continue
            comment_batch.append((comment, comment["embedding"]))
            print(i)

            if i % self.batch_size == 0:
                current_predict,previous_predict=self.getBatchPredict(comment_batch)
                previous_predict_all+=previous_predict
                current_predict_all+=current_predict
                comment_batch = []
                print("comments_processed "+str(i))
                break

        # last batch
        if comment_batch:
            current_predict,previous_predict=self.getBatchPredict(comment_batch)
            previous_predict_all+=previous_predict
            current_predict_all+=current_predict

        return cohen_kappa_score(current_predict_all,previous_predict_all)
    
    
    

    
    def storeResults(self):

        # get training data from MongDB and train
        len_data=super().run_trainer()

        #get stability with this trained model and annotated comments
        stability = self.getStability()
        print(stability)
        model_name = type(self.model).__name__
        current_timestamp = time.time()


        if(os.path.isfile('history.csv')):
            df=pd.read_csv('history.csv')
            df = df.append({'model_name' :model_name,'model_parameters':self.model, 
                                        'time_stamp' :current_timestamp,'label_name':self.labelname,'length_of_annotated':len_data,'stability':stability} , ignore_index=True)
            df.to_csv('history.csv',index=False)

        else:
            df = pd.DataFrame(columns=['model_name', 'model_parameters', 
                                                        'time_stamp','label_name','length_of_annotated','stability'])
            df = df.append({'model_name' :model_name,'model_parameters':self.model, 
                                        'time_stamp' :current_timestamp,'label_name':self.labelname,'length_of_annotated':len_data,'stability':stability} , ignore_index=True)
            df.to_csv('history.csv',index=False)

    
        


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

        
    stability_keeper = StabilityMeasure(labelname,host=args.host, port=args.port)
    stability_keeper.storeResults()


    


