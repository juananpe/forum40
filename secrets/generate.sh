#!/usr/bin/env sh
set -e

if [ ! -f ./jwt_key ]; then
  echo "Generating JWT key"
  openssl rand -out ./jwt_key 32
else
  echo "Using existing JWT key"
fi
