#!/bin/bash

cd ~/forum40
git pull

docker-compose down

docker-compose up --build -d
