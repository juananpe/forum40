FROM postgres:13-alpine

RUN apk add --no-cache build-base python3 python3-dev py3-pip \
  && mkdir /var/lib/postgresql/initdb/ \
  && echo "Downloading OMP corpus…" \
  && wget -qO- https://github.com/OFAI/million-post-corpus/releases/download/v1.0.0/million_post_corpus.tar.bz2 \
     | tar -xj -C /var/lib/postgresql/initdb/ --strip-components 1 "million_post_corpus/corpus.sqlite3" \
  && chown -R postgres:postgres /var/lib/postgresql/initdb/

# Install script dependencies
COPY requirements.txt /root/
RUN python3 -m pip install --no-cache -r /root/requirements.txt

# Source
COPY --chown=postgres:postgres forumdb/ /var/lib/postgresql/initdb/forumdb/

# DB initialization scripts for entrypoint
COPY entrypoint-initdb/ /docker-entrypoint-initdb.d/
