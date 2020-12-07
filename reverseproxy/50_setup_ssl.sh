#!/usr/bin/env sh
set -e

if ! find /etc/nginx/conf.d/ssl/ -mindepth 1 -print -quit 2>/dev/null | grep -q .; then
  echo No custom SSL certificate and pair was provided
  echo Generating a self signed certificate and pair
  openssl req -subj '/CN=localhost' \
    -x509 -newkey rsa:4096 -nodes \
    -keyout /etc/nginx/conf.d/ssl/key.pem \
    -out /etc/nginx/conf.d/ssl/cert.pem \
    -days 365
else
  echo Using the provided SSL certificate and pair
fi
