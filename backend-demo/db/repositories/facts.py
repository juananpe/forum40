from typing import Iterable, Dict, Iterator

from db.repositories.base import BaseRepository


class FactsRepository(BaseRepository):
    def find_by_comment_and_labels(self, comment_ids: Iterable[int], label_ids: Iterable[int]) -> Iterator[Dict]:
        return self._acc.fetch_all(
            'SELECT * FROM facts WHERE comment_id IN %s AND label_id IN %s',
            (tuple(comment_ids), tuple(label_ids)),
        )
