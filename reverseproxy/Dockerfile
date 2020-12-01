FROM nginx:alpine

COPY nginx.conf /etc/nginx/nginx.conf
COPY ssl/mast-se.informatik.uni-hamburg.de-key.pem /etc/nginx/conf.d/key.pem
COPY ssl/mast-se.informatik.uni-hamburg.de-crt.pem /etc/nginx/conf.d/cert.pem
