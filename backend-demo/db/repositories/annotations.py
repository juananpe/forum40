from dataclasses import dataclass

from typing import Iterable, Dict, Optional, Iterator

from db.repositories.base import BaseRepository


@dataclass
class AnnotationCount:
    num_positive: int
    num_negative: int

    @property
    def num_total(self) -> int:
        return self.num_positive + self.num_negative


class AnnotationRepository(BaseRepository):
    def find_all_by_comment_id(self, comment_id: int) -> Iterable[Dict]:
        return self._acc.fetch_all('SELECT * FROM annotations WHERE comment_id = %s', (comment_id,))

    def set_annotation_for_user_comment_label(self, user_id: int, comment_id: int, label_id: int, value: Optional[bool]):
        self._acc.execute(
            'INSERT INTO annotations (user_id, comment_id, label_id, label) '
            'VALUES (%s, %s, %s, %s) '
            'ON CONFLICT (comment_id, label_id, user_id) DO UPDATE SET label = %s',
            (user_id, comment_id, label_id, value, value),
        )

    def count_annotations_on_embedded_comments_for_label(self, label_id: int) -> AnnotationCount:
        result = self._acc.fetch_one(
            'SELECT sum(label::int) pos, sum(1 - label::int) neg '
            'FROM comments c '
            'JOIN annotations a ON c.id = a.comment_id '
            'WHERE a.label_id = %s AND c.embedding IS NOT NULL',
            (label_id,),
        )

        return AnnotationCount(
            num_positive=result['pos'],
            num_negative=result['neg'],
        )

    def count_by_value_for_comments(self, comment_ids: Iterable[int], label_ids: Iterable[int]) -> Iterator[Dict]:
        return self._acc.fetch_all(
            'SELECT comment_id, label_id, sum(label::int) as count_true, sum(1 - label::int) as count_false '
            'FROM annotations '
            'WHERE comment_id IN %s '
            '  AND label_id IN %s '
            'GROUP BY comment_id, label_id',
            (tuple(comment_ids), tuple(label_ids)),
        )

    def find_by_user_for_comments(self, user_id: int, comment_ids: Iterable[int], label_ids: Iterable[int]) -> Iterator[Dict]:
        return self._acc.fetch_all(
            'SELECT * FROM annotations WHERE user_id = %s AND comment_id IN %s AND label_id IN %s',
            (user_id, tuple(comment_ids), tuple(label_ids)),
        )
