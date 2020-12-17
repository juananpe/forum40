from typing import Dict, Iterable, Optional, TypedDict

from db.repositories.base import BaseRepository


class NewLabel(TypedDict):
    type: str
    name: str
    source_id: int
    description: Optional[str]


class LabelRepository(BaseRepository):
    def find_all_by_source_id(self, source_id: int) -> Iterable[Dict]:
        return self._acc.fetch_all('SELECT * FROM labels WHERE source_id = %s', (source_id,))

    def is_name_taken(self, name: str) -> bool:
        return self._acc.fetch_value('SELECT COUNT(*) FROM labels WHERE name = %s', (name,)) > 0

    def insert_label(self, label: NewLabel) -> int:
        return self._acc.fetch_value(
            'INSERT INTO labels (type, name, source_id, description) '
            'VALUES (%(type)s, %(name)s, %(source_id)s, %(description)s) '
            'RETURNING id',
            label,
        )

    def exists(self, id_: int) -> bool:
        return self._acc.fetch_value('SELECT true FROM labels WHERE id = %s LIMIT 1', (id_,), default=False)

    def find_by_id(self, id_: int) -> Dict:
        return self._acc.fetch_one('SELECT * FROM labels WHERE id = %s', (id_,))
