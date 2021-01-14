#!/bin/bash

cd ~/forum40
git pull

docker-compose up --build -d
