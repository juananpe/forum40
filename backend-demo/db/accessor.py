from psycopg2.extras import RealDictCursor
from typing import Optional, Dict, Any, Tuple, TypeVar, Iterator

from db.driver import Connection, Cursor, QueryArgs


class CursorType:
    TUPLE: Cursor[Tuple] = None
    DICT: Cursor[Dict] = RealDictCursor


_no_default = object()

T = TypeVar('T')


class DatabaseAccessor:
    def __init__(self, conn: Connection):
        self.__conn = conn

    def create_cursor(self, type_: Cursor[T] = CursorType.DICT) -> Cursor[T]:
        return self.__conn.cursor(cursor_factory=type_)

    def execute(self, sql: str, args: Optional[QueryArgs] = None):
        with self.create_cursor() as cur:
            cur.execute(sql, args)

    def fetch_one(self, sql: str, args: Optional[QueryArgs] = None) -> Dict[str, Any]:
        with self.create_cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchone()

    def fetch_all(self, sql: str, args: Optional[QueryArgs] = None, batch_size: int = 100) -> Iterator[Dict[str, Any]]:
        with self.create_cursor() as cur:
            cur.execute(sql, args)
            while len(items := cur.fetchmany(size=batch_size)) > 0:
                for item in items:
                    yield item
            return cur.fetchall()

    def fetch_value(self, sql: str, args: Optional[QueryArgs] = None, default=_no_default):
        with self.create_cursor(type_=CursorType.TUPLE) as cur:
            cur.execute(sql, args)
            result = cur.fetchone()
            if result is None and default is _no_default:
                raise Exception('Query did not return a result and no default is set')

            return result[0] if result is not None else default

    def commit(self):
        self.__conn.commit()

    def rollback(self):
        self.__conn.rollback()

    def close(self):
        self.__conn.close()
