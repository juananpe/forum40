from __future__ import annotations

from abc import abstractmethod
from typing import Optional, Tuple, Protocol, TypeVar, Union, Any, Dict, List

# DB API v2.0 Protocol Types (see PEP 249)
# Necessary for type hinting because psycopg2 isn't well typed


QueryArgs = Union[Tuple[Any, ...], Dict[str, Any]]
T = TypeVar('T', )


class Cursor(Protocol[T]):
    @abstractmethod
    def __enter__(self) -> Cursor:
        raise NotImplementedError

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError

    @abstractmethod
    def execute(self, sql: str, args: Optional[QueryArgs] = None):
        raise NotImplementedError

    @abstractmethod
    def fetchone(self) -> T:
        raise NotImplementedError

    @abstractmethod
    def fetchmany(self, size: int = 1) -> List[T]:
        raise NotImplementedError

    @abstractmethod
    def fetchall(self) -> List[T]:
        raise NotImplementedError


S = TypeVar('S')


class Connection(Protocol):
    @abstractmethod
    def __enter__(self) -> Connection:
        raise NotImplementedError

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError

    @abstractmethod
    def cursor(self, cursor_factory: Cursor[S] = Cursor[Tuple]) -> Cursor[S]:
        raise NotImplementedError

    @abstractmethod
    def close(self):
        raise NotImplementedError

    @abstractmethod
    def commit(self):
        raise NotImplementedError

    @abstractmethod
    def rollback(self):
        raise NotImplementedError
