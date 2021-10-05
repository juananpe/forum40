FROM postgres:13

RUN apt-get update \
# build and install pg_cron
  && apt-get install -y \
     wget build-essential postgresql-server-dev-all \
  && wget -qO- https://github.com/citusdata/pg_cron/archive/v1.3.0.tar.gz | tar xzv \
  && cd pg_cron-1.3.0 \
  && make \
  && make install \
  && cd / \
  && rm -rf pg_cron-1.3.0 \
  && apt-get remove -y \
     build-essential postgresql-server-dev-all \
# download omp corpus and precomputed embeddings
  && mkdir /var/lib/postgresql/initdb/ \
  && echo "Downloading OMP corpus…" \
  && wget -qO- https://github.com/OFAI/million-post-corpus/releases/download/v1.0.0/million_post_corpus.tar.bz2 \
     | tar -xj -C /var/lib/postgresql/initdb/ --strip-components 1 "million_post_corpus/corpus.sqlite3" \
  && echo "Downloading pre-computed BERT embeddings for OMP…" \
  && wget -P /var/lib/postgresql/initdb/ https://scan.informatik.uni-hamburg.de/omp_bert_embeddings.hdf5 \
  && chown -R postgres:postgres /var/lib/postgresql/initdb/ \
  && apt-get remove -y \
     wget \
# install python for omp import
  && apt-get install -y --no-install-recommends \
     python3 python3-pip \
  && rm -rf /var/lib/apt/lists/*

# Install script dependencies
COPY requirements.txt /root/
RUN python3 -m pip install --no-cache -r /root/requirements.txt

# Source
COPY --chown=postgres:postgres forumdb/ /var/lib/postgresql/initdb/forumdb/

# DB initialization scripts for entrypoint
COPY entrypoint-initdb/ /docker-entrypoint-initdb.d/
