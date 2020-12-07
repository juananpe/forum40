FROM nginx:alpine

RUN apk add --no-cache openssl

COPY 50_setup_ssl.sh /docker-entrypoint.d/
RUN chmod 744 /docker-entrypoint.d/50_setup_ssl.sh
COPY nginx.conf /etc/nginx/nginx.conf
