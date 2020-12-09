from typing import Dict, Iterable

from db.repositories.base import BaseRepository


class LabelRepository(BaseRepository):
    def find_all_by_source_id(self, source_id: int) -> Iterable[Dict]:
        print('Uses label repository!')
        return self._acc.fetch_all("SELECT * FROM labels WHERE source_id = %s", (source_id,))
