from typing import Dict, Iterator

from db.repositories.base import BaseRepository


class ModelRepository(BaseRepository):
    def current_model_training_sample_count(self, label_id: int) -> int:
        return self._acc.fetch_value(
            'SELECT number_training_samples FROM model WHERE label_id = %s',
            (label_id,),
            default=0,
        )

    def is_training_active(self, label_id: int) -> bool:
        return self._acc.fetch_value(
            'SELECT true FROM model WHERE label_id = %s AND pid IS NOT NULL LIMIT 1',
            (label_id,),
            default=False,
        )

    def find_all_by_label_id(self, label_id: int) -> Iterator[Dict]:
        return self._acc.fetch_all('SELECT * FROM model WHERE label_id = %s', (label_id,))
