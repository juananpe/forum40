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

# Initital steps for the database:

You can either create an empty database or also additionally import the One Million Post corpus data.

1. OMP Database migration or initialization:
- Run the database migration or creation script from this project: https://git.haw-hamburg.de/forum40/databasemigration

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

3. Embedding generation and classification

- The following steps are nessecary to get classification and embedding functionality. Calculating the BERT embeddings for new comments may take some time and can be accelated with a GPU. Once the embeddings are available in the database, training and using classifiers is very fast.

3.1 Embedding Service
- Run embedding container on GPU Cluster
- bind the database port locally with `ssh -L 27017:localhost:27017 <username>@mast-se.informatik.uni-hamburg.de`
- Trigger comment embedding

3.2 Embedding Index
- run embedding container locally
- create embedding index

4. Optional

- You can optionally also use and install the pre-trained meta-comment and offensive-language classification containers:

4.1 Meta-comment classifciation
- Call the endpoint `/classification/unlabeled` to classify meta-comments.

4.2 Offensive-language classification
- Run offensive-language container locally
- bind the database port locally with `ssh -L 27017:localhost:27017 <username>@mast-se.informatik.uni-hamburg.de`
- Trigger classification

The project is live on:

https://mast-se.informatik.uni-hamburg.de/