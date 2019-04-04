#!/bin/bash

cd ~/git/docker-compose
git submodule update --recursive --remote
git pull

docker-compose down

docker-compose up --build