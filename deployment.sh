#!/bin/bash

cd ~/git/forum40
git pull

docker-compose down

docker-compose up --build
