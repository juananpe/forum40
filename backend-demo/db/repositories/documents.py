import datetime

from typing import TypedDict, Optional

from db.repositories.base import BaseRepository


class NewDocument(TypedDict):
    source_id: int
    external_id: str
    url: str
    title: str
    text: str
    timestamp: datetime.datetime
    metadata: str


class DocumentRepository(BaseRepository):
    def find_id_by_external_id(self, source_id: int, external_id: str) -> Optional[int]:
        return self._acc.fetch_value(
            'SELECT id FROM documents WHERE source_id = %s AND external_id = %s LIMIT 1',
            (source_id, external_id),
            default=None,
        )

    def insert(self, document: NewDocument) -> int:
        return self._acc.fetch_value(
            'INSERT INTO documents (source_id, external_id, url, title, text, timestamp, metadata) '
            'VALUES (%(source_id)s, %(external_id)s, %(url)s, %(title)s, %(text)s, %(timestamp)s, %(metadata)s) '
            'RETURNING id',
            document,
        )
