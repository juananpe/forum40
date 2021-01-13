import json
import logging
import psycopg2.extensions
from eventlet.green import select
from typing import Iterator, Dict

from db.connection import db_pool

logger = logging.getLogger(__name__)


def watch_task_updates() -> Iterator[Dict]:
    conn = db_pool.getconn()
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute('LISTEN task_update')

    while True:
        select.select([conn], [], [])
        conn.poll()
        while conn.notifies:
            notify = conn.notifies.pop(0)
            yield json.loads(notify.payload)
