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


https://mast-se.informatik.uni-hamburg.de/