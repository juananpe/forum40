from typing import Dict, TypedDict

from db.repositories.base import BaseRepository


class NewUser(TypedDict):
    name: str
    password: str


class UserRepository(BaseRepository):
    def exists(self, id_: int) -> bool:
        return self._acc.fetch_value('SELECT true FROM users WHERE id = %s LIMIT 1', (id_,), default=False)

    def find_by_id(self, id_: int) -> Dict:
        return self._acc.fetch_one('SELECT * FROM users WHERE id = %s LIMIT 1', (id_,))

    def find_by_name(self, name: str) -> Dict:
        return self._acc.fetch_one('SELECT * FROM users WHERE name = %s LIMIT 1', (name,))

    def insert_user(self, user: NewUser) -> int:
        return self._acc.fetch_value(
            'INSERT INTO users (name, password) '
            'VALUES (%(name)s, %(password)s) '
            'RETURNING id',
            user
        )
