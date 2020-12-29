from contextlib import AbstractContextManager
from psycopg2.extensions import connection
from psycopg2.extras import execute_values
from tqdm import tqdm
from typing import Dict, List, Tuple, Any, Iterable

from forumdb.constants import OmpTables


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def omp_data(sql_conn) -> Dict[OmpTables, List[Dict]]:
    """
    Read the whole sqlite db into a dict
    """
    omp: Dict = {}
    for table in OmpTables:
        cur = sql_conn.cursor()
        cur.execute(f"SELECT * FROM {table.name}")
        omp[table] = cur.fetchall()

    return omp


def embed_data(sql_conn, id) -> Dict[str, List[Dict]]:
    """
    Read the row for provided ID_Post with embeddings into a dict
    """
    embedding: Dict = {}
    cur = sql_conn.cursor()
    cur.execute(f"SELECT * FROM {OmpTables.POSTS.name} WHERE ID_Post = {id}")
    embedding[OmpTables.POSTS] = cur.fetchall()

    return embedding


class Inserter(AbstractContextManager):
    def __init__(self, conn: connection, sql: str, unit: str, total: int):
        self.conn = conn
        self.sql = sql
        self.pbar = tqdm(unit=unit, total=total)
        self.pending = {}
        self.id_lookup: Dict[int, int] = {}

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pbar.close()

    def add(self, source_id: int, args: Tuple[Any, ...]):
        self.pending[source_id] = args

    def add_all(self, argdict: Dict[int, Tuple[Any, ...]]):
        self.pending.update(argdict)

    def _tqdm_relay(self, it: Iterable):
        for i in it:
            yield i
            self.pbar.update(1)

    def flush(self):
        with self.conn.cursor() as cur:
            source_ids = self.pending.keys()
            return_data = execute_values(cur, self.sql, self._tqdm_relay(self.pending.values()), fetch=True)
            target_ids = [d[0] for d in return_data]
            self.pending = {}

            self.id_lookup.update(dict(zip(source_ids, target_ids)))


def insert(conn: connection, sql: str, argdict: Dict[int, Tuple[Any, ...]], unit: str) -> Dict[int, int]:
    with Inserter(conn, sql, unit=unit, total=len(argdict)) as inserter:
        inserter.add_all(argdict)
        inserter.flush()
        return inserter.id_lookup

