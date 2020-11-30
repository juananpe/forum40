FROM nginx:alpine

RUN apk add --no-cache openssl

COPY 50_setup_ssl.sh /docker-entrypoint.d/
COPY nginx.conf /etc/nginx/nginx.conf
