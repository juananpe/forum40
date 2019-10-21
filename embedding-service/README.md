Embedding service
=================

Provides API and fuinctionality for handling embeddings:
* compute embeddings for comment texts (BERT-based)
* index embeddings for fast similarity retrieval (nmslib)
* different retrieval options

CPU-intensive tasks (embedding / indexing) are started as 
celery tasks and can be aborted via the API.


Known bugs
----------

For some reason, the BERT model does not work 
with the `prefork` execution pool. Celery must be started 
with `--pool=solo` option. Unfortunately, this breaks the
tasks/abort funtionality of the API since the termination
signal is not received by the singe-threaded embedding
process.

