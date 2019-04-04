After cloning this repository use:

`git submodule update --init --recursive`

to clone recursive submodules.


To pull all the latest commits of the submodules use: 

`git submodule update --recursive --remote`

For local development environment use:

`docker-compose -f docker-compose_local.yml up --build`