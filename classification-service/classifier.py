import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_validate
from sklearn.model_selection import GridSearchCV
import pickle     

class EmbedClassifier:
    """contains the modules for training and predicting functions"""
    def __init__(self):
        pass

    #take at max 3 minutes on the whole data
    def train(self,embedlabellist,label_name):
        train_X=[]
        train_Y=[]
        for ele in embedlabellist:
            train_X.append(ele[0])
            train_Y.append(ele[1])
        train_X=np.array(train_X)
        train_Y=np.array(train_Y)
        
        # model definition
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
        ## fit procedure
        classifier.fit(train_X,train_Y)

        # Save to file in the current working directory
        path_to_folder= "model"
        pkl_filename = path_to_folder +"/"+"model_"+label_name+".pkl"
        with open(pkl_filename, 'wb') as file:
            pickle.dump(classifier, file)
        return classifier

    def cross_validation(self,embedlabellist,label_name,model):
        train_X=[]
        train_Y=[]
        for ele in embedlabellist:
            train_X.append(ele[0])
            train_Y.append(ele[1])
        train_X=np.array(train_X)
        train_Y=np.array(train_Y)
        
        # model definition
        classifier = model
        ## fit procedure
        scores = cross_validate(classifier, train_X, train_Y, cv=10, scoring=('f1_macro','accuracy'))
        classifier.fit(train_X,train_Y)
        print(scores)
  

        return scores['test_accuracy'].mean(),scores['test_f1_macro'].mean(),scores['fit_time'].mean(),scores['score_time'].mean()
        # Save to file in the current working directory

    def hyperparameter_opt(self,embedlabellist,classifier,grid):

        train_X=[]
        train_Y=[]
        for ele in embedlabellist:
            train_X.append(ele[0])
            train_Y.append(ele[1])
        train_X=np.array(train_X)
        train_Y=np.array(train_Y)
        
        model_cv=GridSearchCV(classifier,grid,cv=10)
        model_cv.fit(train_X,train_Y)
        return model_cv

        
    def predict(self,embedlist,label_name,model=None, get_from_file = True):
        # # Load from file
        if(get_from_file):
            path_to_folder= "model"
            pkl_filename = path_to_folder +"/"+"model_"+label_name+".pkl"
            with open(pkl_filename, 'rb') as file:
                classifier = pickle.load(file)
        else:
            classifier=model    
        # # predict target confidence
        test_X = np.array(embedlist)
        predict_confidence = classifier.predict_proba(test_X)
        return predict_confidence