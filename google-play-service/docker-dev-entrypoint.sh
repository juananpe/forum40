#!/usr/bin/env sh
set -e

if ! find ./node_modules -mindepth 1 -print -quit 2>/dev/null | grep -q .; then
  echo node_modules is empty. Running initial npm install
  npm install
fi

npm run dev
