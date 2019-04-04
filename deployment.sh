#!/bin/bash

cd ~/git/forum40
git submodule update --recursive --remote
git pull

docker-compose down

docker-compose up --build
