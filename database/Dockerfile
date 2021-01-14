FROM postgres:13

RUN apt-get update && apt-get install -y wget python3 python3-pip \
  && rm -rf /var/lib/apt/lists/* \
  && mkdir /var/lib/postgresql/initdb/ \
  && echo "Downloading OMP corpus…" \
  && wget -qO- https://github.com/OFAI/million-post-corpus/releases/download/v1.0.0/million_post_corpus.tar.bz2 \
     | tar -xj -C /var/lib/postgresql/initdb/ --strip-components 1 "million_post_corpus/corpus.sqlite3" \
  && echo "Downloading pre-computed BERT embeddings for OMP…" \
  && wget -P /var/lib/postgresql/initdb/ https://mast-scan.informatik.uni-hamburg.de/omp_bert_embeddings.hdf5 \
  && chown -R postgres:postgres /var/lib/postgresql/initdb/

# Install script dependencies
COPY requirements.txt /root/
RUN python3 -m pip install --no-cache -r /root/requirements.txt

# Source
COPY --chown=postgres:postgres forumdb/ /var/lib/postgresql/initdb/forumdb/

# DB initialization scripts for entrypoint
COPY entrypoint-initdb/ /docker-entrypoint-initdb.d/
