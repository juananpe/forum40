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
docker-compose exec vue npm i
```
This executes the command `npm i` on the frontend container `vue`.
If you expect to run multiple npm commands, you might instead want to launch an interactive shell in the container via
```shell script
docker-compose exec vue sh
```
and run your npm commands there.

## Crawling Realtime Data

- The spon-realtime-crawler project demonstrates how you can incoporate continuous comment import by repeatedly crawling comments from a news website (spiegel.de)

- Clone the https://git.haw-hamburg.de/forum40/spon-realtime-crawler project and follow the installation instructions.

- Change the defaults at the top of the main.py script and insert the username and password that you have created in the previous step. You can also configure the crawling interval.

- You should now be able to see comments appear in your instance in the web browser.

## Embedding generation and classification

- The following steps are nessecary to get classification and embedding functionality. Calculating the BERT embeddings for new comments may take some time and can be accelated with a GPU. Once the embeddings are available in the database, training and using classifiers is very fast. 
- All these processes can be accessed from https://localhost/api/ url, or https://<your_hostname>/api/ if you deployed the application on a server. In the following examples we assume a local installation:

3. Embedding of comments (under Similarity-API :: https://localhost/api/similarity)
- Optional: run embedding container on GPU server and and configure service-URL via `/api/similarity/embeddings/set-service-url`
- Start: `/api/similarity/embeddings/tasks/{taskname}/invoke/{source_id}` by providing taskname as 'embedding' and source_id as 1 (source_id denotes the database source from the available databases) before execute.
- Check progress: `/api/similarity/embeddings/tasks/{taskname}` where taskname is 'embedding'.
- Abort: ``/api/similarity/embeddings/tasks/{taskname}/abort` where taskname is 'embedding'.

4. Indexing of embeddings (under Similarity-API :: https://localhost/api/similarity)
- Start: `/api/similarity/embeddings/tasks/{taskname}/invoke/{source_id}` by providing taskname as 'indexing' and source_id as 1 before execute.
- Check progress: `/api/similarity/embeddings/tasks/{taskname}` where taskname is 'indexing'.
- Abort: ``/api/similarity/embeddings/tasks/{taskname}/abort` where taskname is 'indexing'.

5. Classification of comments (under Classification-API :: https://localhost/api/classification)
- Create a new label in the front-end (needs login), add some training data (minimum 25 positive and negative examples per category)
- Train a model and classify all comments of a specific source_id for each labelname one by one: `/api/classification/classification/update`
- Get information about training progress: `/api/classification/classification/history`: contains timestamp, task, label, training set size, cv acc, cv f1, stability score, duration as CSV


## Incremental database updates

Embedding, indexing and classification should work with incremental comments in the database. We may run cron jobs for:
* Every m minutes: crawling comments
* Every m minutes: embedding comments
* Every m minutes: indexing comments
* ???: classification of comments only when there are new comments! [not working yet]


## Links

- [Mockups](https://drive.google.com/file/d/1dHhMLJ3wGDxC2tQtV3n5kjjxIm-DBiaC/view?usp=sharing)
- [Live Demo](https://mast-se.informatik.uni-hamburg.de/)
