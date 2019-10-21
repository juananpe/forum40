Embedding service
=================

Provides API and fuinctionality for handling embeddings:
* compute embeddings for comment texts (BERT-based)
* index embeddings for fast similarity retrieval (nmslib)
* different retrieval options

CPU-intensive tasks (embedding / indexing) are started as 
celery tasks and can be aborted via the API.

Caution: for some reason, the BERT model does not work 
with the `prefork` execution pool. Cenelry must be started 
with `--pool=solo` option.

