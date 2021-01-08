import numpy as np
import pickle
import sys
import torch
import torch.nn as nn
import torch.optim as optim
import random
from torch.utils.data import Dataset, DataLoader, TensorDataset
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_validate, KFold
from sklearn.metrics import f1_score
from timeit import default_timer as timer

models_path = "models"


def get_model_path(label_name):
    return models_path + "/" + "model_" + label_name + ".pkl"


def get_model_path_torch(label_name):
    return models_path + "/" + "model_" + label_name + ".pt"


def get_history_path(label_name):
    return models_path + "/" + "history_" + label_name + ".csv"


class EmbeddingClassifier:
    """contains the modules for training and predicting functions"""

    def __init__(self, classifier=None, nn=False):
        if nn:
            self.classifier = self.get_nn_classifier()
        elif classifier:
            self.classifier = classifier
        else:
            self.classifier = self.get_lr_classifier()

    def get_nn_classifier(self, embedding_dim=768, classes=1):
        model = nn.Sequential(nn.Linear(embedding_dim, 512),
                              nn.ReLU(),
                              nn.Linear(512, 256),
                              nn.ReLU(),
                              nn.Dropout(p=0.25),
                              nn.Linear(256, 128),
                              nn.ReLU(),
                              nn.Dropout(p=0.25),
                              nn.Linear(128, classes),
                              nn.Sigmoid(),
                              )
        return model

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

    def train_nn(self, dataset, label_name):
        losses = []
        batch_size = 50
        epochs = 50
        total_train_acc = 0
        total_test_acc = 0
        f_score_stack = 0
        kfold = KFold(n_splits=5)

        loss_function = nn.BCELoss()  # reduction is mean
        optimizer = optim.Adam(self.classifier.parameters(), lr=0.001, weight_decay=0.0001)  # weight_deacy=L2 Regularization

        train_X = []
        train_Y = []
        random.shuffle(dataset)

        for entry in dataset:
            train_X.append(entry[0])
            train_Y.append(entry[1])

        train_X = np.array(train_X)
        train_Y = np.array(train_Y)

        start = timer()

        print("\n\nNeural Network detailed training information...\n")
        for fold, (train_index, test_index) in enumerate(kfold.split(train_X, train_Y)):
            # Dividing data into folds
            x_train_fold = train_X[train_index]
            x_test_fold = train_X[test_index]
            y_train_fold = train_Y[train_index]
            y_test_fold = train_Y[test_index]
            print("Training data split ratio [online offline]: {}".format(np.bincount(y_train_fold)))
            print("Testing data split ratio [online offline]: {}".format(np.bincount(y_test_fold)))

            train_X_tensor = torch.tensor(x_train_fold, dtype=torch.float)
            train_Y_tensor = torch.tensor(y_train_fold, dtype=torch.float)
            test_X_tensor = torch.tensor(x_test_fold, dtype=torch.float)
            test_Y_tensor = torch.tensor(y_test_fold, dtype=torch.float)

            train_dataset = TensorDataset(train_X_tensor, train_Y_tensor)
            train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=False)
            test_dataset = TensorDataset(test_X_tensor, test_Y_tensor)
            test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

            # Resetting the parameters for each fold so that weights won't be accumulated each fold
            for layer in self.classifier.children():
                if hasattr(layer, 'reset_parameters'):
                    layer.reset_parameters()

            for epoch in range(epochs):
                if (epoch + 1) % 10 == 0:
                    print('\nEpoch {} / {} \nFold number {} / {}'.format(epoch + 1, epochs, fold + 1, kfold.get_n_splits()))
                correct = 0
                total_train_loss = 0
                self.classifier.train()
                for i, (data, labels) in enumerate(train_loader):
                    optimizer.zero_grad()
                    # Run the forward pass
                    predictions = self.classifier(data)
                    # Compute loss function
                    loss = loss_function(predictions, labels.unsqueeze(1))
                    # Do the backward pass and update the gradient
                    loss.backward()
                    optimizer.step()
                    total_train_loss += loss.item()
                    pred = torch.round(predictions.squeeze())
                    correct += (pred == labels).sum()

                losses.append(total_train_loss)
                if (epoch + 1) % 10 == 0:
                    print('[{}/{} ({:.0f}%)]\tLoss: {:.6f}\t Accuracy:{:.3f}%'.format(
                        (i + 1) * len(data), len(train_loader.dataset),
                        100. * (i + 1) / len(train_loader), loss.data,
                        float(correct * 100) / float(len(train_loader.dataset))))
                    print("Epoch: {}, Total Loss: {:.6f}".format(epoch + 1, total_train_loss))

            total_train_acc += float(correct * 100) / float(len(train_loader.dataset))

            correct = 0
            np_all_pred = []
            np_all_labels = []
            self.classifier.eval()
            with torch.no_grad():
                for i, (data, labels) in enumerate(test_loader):
                    predictions = self.classifier(data)
                    pred = torch.round(predictions.squeeze())
                    correct += (pred == labels).sum()
                    if len(np_all_pred) == 0:
                        np_all_pred = pred.detach().cpu().numpy()
                        np_all_labels = labels.detach().cpu().numpy()
                    else:
                        np_all_pred = np.hstack((np_all_pred, pred.detach().cpu().numpy()))
                        np_all_labels = np.hstack((np_all_labels, labels.detach().cpu().numpy()))
            np_all_pred = np_all_pred.astype(np.int32)
            np_all_labels = np_all_labels.astype(np.int32)
            f_score_stack += f1_score(np_all_labels, np_all_pred, average="binary", pos_label=1)
            test_acc = float(correct * 100) / float(len(test_loader.dataset))
            total_test_acc += test_acc
            print('\nTest Accuracy at KFold-{}: {:.3f}%\n'.format(fold + 1, test_acc))

        end = timer()

        total_train_acc = (total_train_acc / kfold.get_n_splits())
        total_test_acc = (total_test_acc / kfold.get_n_splits())
        f_score_stack = (f_score_stack/kfold.get_n_splits())
        training_time = (end-start)

        print("-" * 60)
        print("*Model information (averaged) after {}-Fold Cross Validation*".format(kfold.get_n_splits()))
        print("-" * 60)
        print('Train accuracy: {:.3f}%'.format(total_train_acc))
        print('Test accuracy: {:.3f}%'.format(total_test_acc))
        print('Test F1_score: {:.3f}%'.format(f_score_stack))
        print('Model training time (seconds): {}\n'.format(training_time))
        print("-" * 60)

        # Save to file in the current working directory
        pt_filename = get_model_path_torch(label_name)
        torch.save(self.classifier.state_dict(), pt_filename)
        return self.classifier, total_test_acc, f_score_stack, training_time

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
