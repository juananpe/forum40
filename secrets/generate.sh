#!/usr/bin/env sh
set -e

if [ ! -f ./jwt_key ]; then
  echo "Generating JWT key"
  openssl rand -out ./jwt_key 32
else
  echo "Using existing JWT key"
fi

if [ ! -f ./db_password.txt ]; then
  echo "Generating database password"
  pwgen -s 32 1 | tr -d '\n' > ./db_password.txt
else
  echo "Using existing database password"
fi
