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


###importing classifier 
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import RBF
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis



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

class PerformEvaluator(RunClassifier):
    
    def runOptimizer(self,classifier,param_dict):
        annotation_dataset=super().collect_trainingdata()
        self.classification_model = EmbedClassifier()
        optimized_model=self.classification_model.hyperparameter_opt(annotation_dataset,classifier,param_dict)
        print("tuned hyperparameters:" ,logreg_cv.best_params_)        
        print("accuracy",logreg_cv.best_score)



    def storeResults(self,classifier):

        # get training data from MongDB
        accuracy,f1_score,fit_time,score_time,len_data=super().run_trainer(classifier)

        model_name = type(classifier).__name__
        current_timestamp = time.time()


        if(os.path.isfile('performance.csv')):
            df=pd.read_csv('performance.csv')
            df = df.append({'model_name' :model_name,'model_parameters':classifier, 
                                        'time_stamp' :current_timestamp,'label_name':self.labelname,'cross_val_f1_score':f1_score,
                                        'cross_val_acc_score':accuracy,'time_to_fit':fit_time,'time_to_score':score_time} , ignore_index=True)
            df.to_csv('performance.csv',index=False)

        else:
            df = pd.DataFrame(columns=['model_name', 'model_parameters', 
                                                        'time_stamp','label_name','cross_val_f1_score','cross_val_acc_score','time_to_fit','time_to_score'])
            df = df.append({'model_name' :model_name,'model_parameters':classifier,'time_stamp' :current_timestamp,
                            'label_name':self.labelname,'cross_val_f1_score':f1_score,'cross_val_acc_score':accuracy,
                            'time_to_fit':fit_time,'time_to_score':score_time} , ignore_index=True)
            df.to_csv('performance.csv',index=False)


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

        
    eval_perform = PerformEvaluator(labelname,host=args.host, port=args.port,cross_val=True)

    #classifier = 
    
    # classifiers = [
    # KNeighborsClassifier(3),
    # SVC(kernel="linear", C=0.025,class_weight='balanced'),
    # SVC(gamma=2, C=1,class_weight='balanced'),
    # DecisionTreeClassifier(max_depth=5,class_weight='balanced'),
    # RandomForestClassifier(max_depth=5, n_estimators=10, max_features=1,class_weight='balanced'),
    # MLPClassifier(alpha=1, max_iter=1000),
    # GaussianNB(),
    # LogisticRegression(n_jobs=10,random_state=42,class_weight='balanced',solver='saga',penalty= 'elasticnet',tol=0.001,max_iter=200,C=1.0,l1_ratio=0.1)]


    # for classifier in classifiers:
    #     eval_perform.storeResults(classifier)



    classifier = LogisticRegression()
    grid_params = [{
                    "C":np.linspace(-3,3,7),
                    "penalty":["elasticnet"],
                    "class_weight":['balanced'],
                    "solver":["saga"],
                    "max_iter":np.linspace(100,1000,100),
                    "penalty_ratio":np.linspace(0,1,10)


 
                },
                {
                    "C":np.linspace(-3,3,7),
                    "penalty":[None],
                    "class_weight":['balanced'],
                    "solver":["saga"],
                    "max_iter":np.linspace(100,1000,100),
                    

 
                },
                {
                    "C":np.linspace(-3,3,7),
                    "penalty":["l2",None],
                    "class_weight":['balanced'],
                    "solver":["newton-cg", "lbfgs", "sag" ],
                    "max_iter":np.linspace(100,1000,100),
                    

 
                },
                {
                    "C":np.linspace(-3,3,7),
                    "penalty":["l1"],
                    "class_weight":['balanced'],
                    "solver":["liblinear" ],
                    "max_iter":np.linspace(100,1000,100),
                   

 
                }
                ]

    eval_perform.runOptimizer(classifier,grid_params)