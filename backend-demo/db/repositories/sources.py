from typing import TypedDict, Dict

from db.repositories.base import BaseRepository


class NewSource(TypedDict):
    name: str
    domain: str


class SourceRepository(BaseRepository):
    def find_all(self, include_protected: bool = True):
        query = 'SELECT * FROM sources'
        if not include_protected:
            query += ' WHERE protected = FALSE'

        return self._acc.fetch_all(query)

    def find_by_name(self, name: str) -> Dict:
        return self._acc.fetch_one('SELECT * FROM sources WHERE name = %s', (name,))

    def insert(self, source: NewSource) -> int:
        return self._acc.fetch_value(
            'INSERT INTO sources (name, domain) '
            'VALUES (%(name)s, %(domain)s) '
            'RETURNING id',
            source,
        )
