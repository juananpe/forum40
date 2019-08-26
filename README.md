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

Initital steps for the database:

1. OMP Database migration
- Run the database migration project:

https://gitlab.informatik.haw-hamburg.de/forum40/databasemigration

2. Meta-comment classifciation
- Call the endpoint `/classification/unlabeled` to classify meta-comments.

3. Offensive-language classification
- Run offensive-language container locally
- bind the database port locally with `ssh -L 27017:localhost:27017 <username>@mast-se.informatik.uni-hamburg.de`
- Trigger classification

4. Embedding Service
- Run embedding container on GPU Cluster
- bind the database port locally with `ssh -L 27017:localhost:27017 <username>@mast-se.informatik.uni-hamburg.de`
- Trigger comment embedding

5. Embedding Index
- run embedding container locally
- create embedding index



The project is live on:

https://mast-se.informatik.uni-hamburg.de/