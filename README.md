# Forum 4.0

Install the npm modules in the `frontend` project with:

```bash
cd frontend-demo
npm install
```

Create self-signed certificate files with:

```openssl req -subj '/CN=localhost' -x509 -newkey rsa:4096 -nodes -keyout key.pem -out cert.pem -days 365```

and move the created files into `reverseproxy/docker_ssl_proxy`.

For local development environment use:

`docker-compose -f docker-compose.yml -f docker-compose.local.yml up --build`

If you have problems with the vue container ("sh: vue-cli-service: not found" or similar), you may need to install npm locally on your host system and run:

```cd frontend-demo; npm run build```

once.

## Initital steps for the database:

You can either create an empty database or also additionally import the One Million Post corpus data.

1. OMP Database migration or initialization:
- Run the database migration or creation script from this project: https://git.haw-hamburg.de/forum40/databasemigration

```psql -d omp -h localhost -p 5432 --username=postgres --password``` < init.sql 

- After succesfully creating the database schema, you may want to add a user to the database:

```psql -d omp -h localhost -p 5432 --username=postgres --password ```

- type the password 'postgres' when promted. Then insert a user into the users table, e.g.:

```omp=# insert into users values (0,0,'ben',0,'hunter2','admin');```

- This inserts the admin user 'ben' with the passowrd 'hunter2' into the database.

- You should now be able to load the tool on https://localhost/ (or the remote hostname) and you should be able to use the login you have just created. You may need to add an exception for the self signed browser certificate.

2. Crawling realtime data:

- The spon-realtime-crawler project demonstrates how you can incoporate continuous comment import by repeatedly crawling comments from a news website (spiegel.de)

- Clone the https://git.haw-hamburg.de/forum40/spon-realtime-crawler project and follow the installation instructions.

- Change the defaults at the top of the main.py script and insert the username and password that you have created in the previous step. You can also configure the crawling interval.

- You should now be able to see comments appear in your instance in the web browser.

## Embedding generation and classification

- The following steps are nessecary to get classification and embedding functionality. Calculating the BERT embeddings for new comments may take some time and can be accelated with a GPU. Once the embeddings are available in the database, training and using classifiers is very fast.

3. Embedding of comments
- Optional: run embedding container on GPU server and and configure service-URL via `/api/similarity/embeddings/set-service-url`
- Start: `/api/similarity/embeddings/embedding/invoke/1` for source_id 1
- Check progress: `/api/similarity/embeddings/embedding`
- Abort: ``/api/similarity/embeddings/embedding/abort`

4. Indexing of embeddings
- Start: `/api/similarity/embeddings/indexing/invoke/1` for source_id 1
- Check progress: `/api/similarity/embeddings/indexing`
- Abort: ``/api/similarity/embeddings/indexing/abort`

5. Classification of comments
- Create a new label in the front-end (needs login), add some training data (minimum 25 positive and negative examples per category)
- Train a model and classify all comments of a specific source_id: `/api/classification/classification/update`
- Get information about training progress: `/api/classification/classification/history`: contains timestamp, task, label, training set size, cv acc, cv f1, stability score, duration as CSV


## Incremental database updates

Embedding, indexing and classification should work with incremental comments in the database. We may run cron jobs for:
* Every m minutes: crawling comments
* Every m minutes: embedding comments
* Every m minutes: indexing comments
* ???: classification of comments only when there are new comments! [not working yet]

## Demo

The project is live on:

https://mast-se.informatik.uni-hamburg.de/