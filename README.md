# Forum 4.0
For local development use
```shell script
docker-compose -f docker-compose.yml -f docker-compose.local.yml up --build
```

The first start might take a few minutes.
During this time, comments and articles from the Austrian newspaper "Der Standard" published in the  [One Million Post Corpus](https://ofai.github.io/million-post-corpus/) are imported.

After the initialization, you should be able to use the tool at https://localhost/.

To install or update frontend dependencies, you have to use the npm installation of the frontend container.
For example, to update the dependencies after a git pull, you would run
```shell script
docker-compose exec frontend npm i
```
This executes the command `npm i` on the frontend container `frontend`.
If you expect to run multiple npm commands, you might instead want to launch an interactive shell in the container via
```shell script
docker-compose exec frontend sh
```
and run your npm commands there.


## Embedding generation and classification
After loading new comments into the database, it is necessary to generate embeddings for them before they can be used for classification and the similar comment search functionality.
The embedding generation has to be triggered via the API, which can be accessed interactively from the `/api/` subpath, i.e. on `http://mast-se.informatik.uni-hamburg.de/api/` for the demo deployment or `http://localhost/api/` for a local instance.

Generating new embeddings may take a while, but can be accelerated by running the embedding service on a GPU compute node.
If you have deployed the embedding service externally, use the `/api/similarity/embeddings/set-service-url` method to change the instance of the embedding service
that the Forum 4.0 backend should use.

To generate embeddings for new comments, use the `/api/similarity/embeddings/source/{source_id}/embed` API method.
After the embedding generation finishes, you can classify them and run indexing on the embeddings to enable similar comment search.
To run classification for one label, call `/api/classification/classification/update`.
To index the new comments, call `/api/similarity/embeddings/source/{source_id}/index`.


## Links

- [Mockups](https://drive.google.com/file/d/1dHhMLJ3wGDxC2tQtV3n5kjjxIm-DBiaC/view?usp=sharing)
- [Live Demo](https://mast-se.informatik.uni-hamburg.de/)
