FROM alpine:latest

RUN apk add --no-cache openssl pwgen
COPY ./generate.sh /root/generate.sh
RUN chmod 744 /root/generate.sh

WORKDIR /root/store
CMD ["/root/generate.sh"]
