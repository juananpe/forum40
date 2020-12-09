from __future__ import annotations

from contextlib import contextmanager

import wrapt

from db.accessor import DatabaseAccessor
from db.connection import db_pool
from db.driver import Connection
from db.repositories import AnnotationRepository, DocumentRepository, ModelRepository, \
    CommentRepository, LabelRepository, SourceRepository, UserRepository


class Database:
    def __init__(self, connection: Connection):
        self.acc: DatabaseAccessor = DatabaseAccessor(connection)

    @staticmethod
    @contextmanager
    def connect():
        conn: Connection = db_pool.getconn()
        try:
            yield Database(conn)
        except:
            conn.rollback()
            raise
        else:
            conn.commit()
        finally:
            db_pool.putconn(conn)

    @property
    def annotations(self) -> AnnotationRepository:
        return AnnotationRepository(accessor=self.acc)

    @property
    def documents(self) -> DocumentRepository:
        return DocumentRepository(accessor=self.acc)

    @property
    def models(self) -> ModelRepository:
        return ModelRepository(accessor=self.acc)

    @property
    def comments(self) -> CommentRepository:
        return CommentRepository(accessor=self.acc)

    @property
    def labels(self) -> LabelRepository:
        return LabelRepository(accessor=self.acc)

    @property
    def sources(self) -> SourceRepository:
        return SourceRepository(accessor=self.acc)

    @property
    def users(self) -> UserRepository:
        return UserRepository(accessor=self.acc)


@wrapt.decorator
def with_database(wrapped, instance, args, kwargs):
    with Database.connect() as db:
        return wrapped(db, *args, **kwargs)

