import logging
import psycopg2
import time
from psycopg2.pool import ThreadedConnectionPool
from threading import Lock
from typing import Optional

from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from db.driver import Connection

logger = logging.getLogger(__name__)


class WaitingConnectionPool:
    def __init__(self, minconn: int, maxconn: int, *args, **kwargs):
        self.minconn = minconn
        self.maxconn = maxconn
        self.args = args
        self.kwargs = kwargs
        self._pool: Optional[ThreadedConnectionPool] = None
        self._lock = Lock()

    def _get_pool(self) -> ThreadedConnectionPool:
        with self._lock:
            while self._pool is None or self._pool.closed:
                try:
                    self._pool = ThreadedConnectionPool(self.minconn, self.maxconn, *self.args, **self.kwargs)
                except psycopg2.OperationalError as e:
                    if e.pgerror is not None:
                        # not a connection error. Only want to retry if server is currently
                        # unavailable, not if e.g. password is wrong
                        raise

                    logger.info('Connection to database failed. Retrying in 3 seconds')
                    time.sleep(3)

            return self._pool

    def getconn(self) -> Connection:
        return self._get_pool().getconn()

    def putconn(self, conn: Connection):
        if self._pool is not None and not self._pool.closed:
            self._pool.putconn(conn)


db_pool = WaitingConnectionPool(10, 50, host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
