Classifier service
==================

Contains classes and API to train a LR model on top of pre-computed embeddings.

1. Train a model:
```
python train.py --labelname=OffTopic
```

2. Update labels in DB:
```
python update.py --labelname=OffTopic
```

Todo
----

Save training history (timestamp, training set size, cv result, stability score)