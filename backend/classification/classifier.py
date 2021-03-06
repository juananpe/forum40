import numpy as np
import pickle
import sys
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_validate

models_path = "models"


def get_model_path(label_name):
    return models_path + "/" + "model_" + label_name + ".pkl"


def get_history_path(label_name):
    return models_path + "/" + "history_" + label_name + ".csv"


class EmbeddingClassifier:
    """contains the modules for training and predicting functions"""

    def __init__(self, classifier=None):
        if classifier:
            self.classifier = classifier
        else:
            self.classifier = self.get_lr_classifier()

    def get_lr_classifier(self):
        return LogisticRegression(
            n_jobs=-1,
            random_state=42,
            class_weight='balanced',
            solver='saga',
            penalty='elasticnet',
            tol=0.0001,
            max_iter=100,
            C=1.0,
            l1_ratio=0.5
        )

    def load_from_disk(self, label):
        pkl_filename = get_model_path(label)
        with open(pkl_filename, 'rb') as file:
            classifier = pickle.load(file)
        self.classifier = classifier

    def set_c(self, C):
        self.classifier.C = C

    # take at max 3 minutes on the whole data
    def train(self, dataset, label_name):

        data_len = len(dataset)
        assert(data_len > 0)
        emb_dim = len(dataset[0][0])

        train_X = np.zeros((data_len, emb_dim))
        train_Y = np.zeros(data_len, dtype=np.int32)

        for i, entry in enumerate(dataset):
            train_X[i] = entry[0]
            train_Y[i] = entry[1]

        print("Embedding dim is:", emb_dim)
        print(f'Set of training for label ({label_name}) {train_X.shape}', file=sys.stderr)
        print(f'Training set label distribution:', np.bincount(train_Y))

        # fit procedure
        self.classifier.fit(train_X, train_Y)

        # Save to file in the current working directory
        pkl_filename = get_model_path(label_name)
        with open(pkl_filename, 'wb') as file:
            pickle.dump(self.classifier, file)
        return self.classifier

    def cross_validation(self, dataset, k=5):
        data_len = len(dataset)
        assert(data_len > 0)
        emb_dim = len(dataset[0][0])

        train_X = np.zeros((data_len, emb_dim))
        train_Y = np.zeros(data_len, dtype=np.int32)

        for i, entry in enumerate(dataset):
            train_X[i] = entry[0]
            train_Y[i] = entry[1]

        print("Embedding dim is:", emb_dim)
        print(f'Set of training {train_X.shape}', file=sys.stderr)
        print(f'Training set label distribution:', np.bincount(train_Y))

        # fit procedure
        scores = cross_validate(self.classifier, train_X, train_Y, cv=k, scoring=('f1_macro', 'accuracy'))

        return (
            scores['test_accuracy'].mean(),
            scores['test_f1_macro'].mean(),
            scores['fit_time'].mean(),
            scores['score_time'].mean()
        )

    def predict(self, embedlist):
        # predict target confidence
        test_X = np.array(embedlist)
        confidence = self.classifier.predict_proba(test_X)
        labels = [True if label == 1 else False for label in np.argmax(confidence, axis=1).tolist()]
        return labels, confidence[:, 1].tolist()
