FROM alpine:latest

RUN apk add --no-cache openssl
COPY ./generate.sh /root/generate.sh

WORKDIR /root/store
CMD ["/root/generate.sh"]
