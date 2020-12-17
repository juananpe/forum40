from typing import Dict

from db.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def exists(self, id_: int) -> bool:
        return self._acc.fetch_value('SELECT true FROM users WHERE id = %s LIMIT 1', (id_,), default=False)

    def find_by_name(self, name: str) -> Dict:
        return self._acc.fetch_one('SELECT * FROM users WHERE name = %s LIMIT 1', (name,))
