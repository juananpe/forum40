#!/usr/bin/env bash

cd /var/lib/postgresql/initdb/
python3 -m forumdb.load_omp
