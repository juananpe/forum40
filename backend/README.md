Backend APIs
============

This service provides back-end functionality for the user comments analysis tool.

Database access for the front-end
---------------------------------

to be described ...


Similarity for comments
----------------------

Access: `/api/similarity`

Embedding and indexing are long running tasks which are startet via API calls but run as python sub processes (apis.utils.taks.ForumProcessor).

Tasks must be started with respect to a given source id `/embeddings/tasks/{taskname}/invoke/{source_id}`, first embedding, then indexing.

### Compute embeddings

Text comments in the database are converted into embeddings via an external service.

This external service is the embedding-service in this docker-compose setup (embedding container), or the container in a separate server, e.g. a GPU server for faster embedding (GPU speeds up embedding by factor 15 or so).

Per default, the service is set to `http://embedding:5060/embed`. By calling the API `/api/similarity/set-service-url` it can bet set, e.g. to `http://ltdemos.informatik.uni-hamburg.de/embedding-service` which forwards to ltgpu1 where a GPU-based instance can be started.

Embeddings will be computed via API calls and stored along with comment texts in the comments table of the DB by calling this URL:

Example: `/embeddings/tasks/embedding/invoke/1`


### Similarity search

To be able to search for similar comments, comment embeddings have to be indexed.

Example: start indexing of source 3 `/embeddings/tasks/indexing/invoke/3`

One index per source_id is saved in the `models` directory.

New embeddings can be added to the index incrementally.

After a new index has been created, or an existing index has been extended, it must be reloaded by the app. The index script `embeddings_index.py` will try to do that automatically by calling 

`/embeddings/reload-index/3`


Classification of comments
--------------------------

Access: `/api/classification`

Based on embeddings, a linear regression classifier can be trained for arbitraty categories.

Simply call the `/update` API.

The `/history` API stores information about the progress of training a specific category.


