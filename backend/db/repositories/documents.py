import datetime

from typing import TypedDict, Optional, Dict, Set, Iterator, Any

from db.repositories.base import BaseRepository


class NewDocument(TypedDict):
    source_id: int
    external_id: str
    url: str
    title: str
    text: str
    timestamp: datetime.datetime
    metadata: str
    category: Optional[str]


base_document_fields = frozenset({'id'})


def document_fields(content: bool = False, metadata: bool = False, embedding: bool = False) -> Set[str]:
    fields = set(base_document_fields)
    if metadata:
        fields |= {'source_id', 'external_id', 'timestamp', 'category', 'url', 'metadata'}
    if content:
        fields |= {'title', 'text', 'markup'}
    if embedding:
        fields |= {'embedding'}
    return fields


class DocumentRepository(BaseRepository):
    def find_by_id(self, id_: int, fields: Set[str] = base_document_fields) -> Dict:
        return self._acc.fetch_one(f'SELECT {", ".join(fields)} FROM documents WHERE id = %s', (id_,))

    def find_id_by_external_id(self, source_id: int, external_id: str) -> Optional[int]:
        return self._acc.fetch_value(
            'SELECT id FROM documents WHERE source_id = %s AND external_id = %s LIMIT 1',
            (source_id, external_id),
            default=None,
        )

    def find_all_by_source_id(
            self,
            source_id: int,
            limit: int = 100,
            skip: int = 0,
            fields: Set[str] = base_document_fields
    ) -> Iterator[Dict[str, Any]]:
        return self._acc.fetch_all(
            f'SELECT {", ".join(fields)} FROM documents WHERE source_id = %s LIMIT %s OFFSET %s',
            (source_id, limit, skip)
        )

    def insert(self, document: NewDocument) -> int:
        return self._acc.fetch_value(
            'INSERT INTO documents (source_id, external_id, url, title, text, timestamp, category, metadata) '
            'VALUES (%(source_id)s, %(external_id)s, %(url)s, %(title)s, %(text)s, %(timestamp)s, %(category)s, %(metadata)s) '
            'RETURNING id',
            document,
        )
