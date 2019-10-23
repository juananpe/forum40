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

* app.py: Celery (or other task scheduler)
* Save training history (timestamp, task, label, training set size, cv result, stability score)
* Process to update only specific ids (e.g. the current comments displayed in the UI)