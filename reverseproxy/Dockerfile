FROM nginx:alpine
 
COPY nginx.conf /etc/nginx/nginx.conf
COPY docker_ssl_proxy/key.pem /etc/nginx/conf.d/key.pem
COPY docker_ssl_proxy/cert.pem /etc/nginx/conf.d/cert.pem