from enum import Enum

import os

OMP_DB_FILE = 'corpus.sqlite3'
OMP_EMBEDDINGS_FILE = 'omp_bert_embeddings.hdf5'

PG_USER = os.environ['POSTGRES_USER']
PG_DB = os.environ['POSTGRES_DB']


class OmpTables(Enum):
    ANNOTATIONS = "Annotations"
    CATEGORIES = "Categories"
    POSTS = "Posts"
    ANNOTATIONS_CONSOLIDATED = "Annotations_consolidated"
    CROSSVALSPLIT = "CrossValSplit"
    ARTICLES = "Articles"
    NEWSPAPER_STAFF = "Newspaper_Staff"

    @property
    def name(self) -> str:
        return self.value
