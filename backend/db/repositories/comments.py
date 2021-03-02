from dataclasses import dataclass
from enum import IntEnum

import datetime
from psycopg2.extras import execute_values
from pypika import PostgreSQLQuery, Table, Order, Criterion, functions as pfn
from typing import Iterable, Dict, Optional, Union, TypedDict, List, Set, Iterator

from db.repositories.base import BaseRepository
from db.repositories.util import QueryArguments


class NewComment(TypedDict):
    source_id: Optional[int]
    external_id: Optional[str]
    doc_id: Optional[int]
    timestamp: datetime.datetime
    user_id: Optional[int]
    parent_comment_id: Optional[int]
    status: Optional[str]
    title: Optional[str]
    text: Optional[str]
    embedding: Optional[List[float]]


@dataclass
class TimestampSorting:
    order: Order


class UncertaintyOrder:
    pass


@dataclass
class FactSorting:
    label_id: int
    order: Union[Order, UncertaintyOrder]


class Granularity(IntEnum):
    YEAR = 1
    MONTH = 2
    DAY = 3


base_comment_fields = frozenset({'id'})


def comment_fields(content: bool = False, metadata: bool = False, embedding: bool = False) -> Set[str]:
    fields = set(base_comment_fields)
    if metadata:
        fields |= {'source_id', 'external_id', 'doc_id', 'parent_comment_id', 'user_id', 'status', 'timestamp'}
    if content:
        fields |= {'title', 'text'}
    if embedding:
        fields |= {'embedding'}
    return fields


class CommentRepository(BaseRepository):
    def exists(self, id_: int) -> bool:
        return self._acc.fetch_value('SELECT true FROM comments WHERE id = %s LIMIT 1', (id_,), default=False)

    def count_by_category_for_source(self, source_id: int) -> Iterator[Dict]:
        return self._acc.fetch_all(
            'SELECT name category_name, value comment_count FROM count_comments_by_category WHERE source_id = %s',
            (source_id,),
        )

    def insert(self, comment: NewComment) -> int:
        ts = comment['timestamp']
        return self._acc.fetch_value(
            'INSERT INTO comments (source_id, external_id, doc_id, timestamp, year, month, day, user_id, parent_comment_id, status, title, text, embedding) '
            'VALUES (%(source_id)s, %(external_id)s, %(doc_id)s, %(timestamp)s, %(year)s, %(month)s, %(day)s, %(user_id)s, %(parent_comment_id)s, %(status)s, %(title)s, %(text)s, %(embedding)s) '
            'RETURNING id',
            comment | {'year': ts.year, 'month': ts.month, 'day': ts.day},
        )

    def insert_many(self, comments: List[NewComment]) -> List[int]:
        items = [
            (c['source_id'], c['external_id'], c['doc_id'], c['timestamp'],
             c['timestamp'].year, c['timestamp'].month, c['timestamp'].day,
             c['user_id'], c['parent_comment_id'], c['status'], c['title'],
             c['text'], c['embedding'])
            for c in comments
        ]

        with self._acc.create_cursor() as cur:
            query = (
                'INSERT INTO comments (source_id, external_id, doc_id, timestamp, year, month, day, user_id, parent_comment_id, status, title, text, embedding) '
                'VALUES %s '
                'RETURNING id'
            )

            results = execute_values(cur, query, items, fetch=True)

        return [result['id'] for result in results]

    def find_all_by_query(
            self,
            source_id: int,
            keywords: Optional[Iterable[str]] = None,
            sorting: Union[TimestampSorting, FactSorting] = TimestampSorting(Order.desc),
            document_category: Optional[str] = None,
            fields: Set[str] = base_comment_fields,
            limit: int = 100,
            offset: int = 0,
    ) -> Iterator[Dict]:
        args = QueryArguments()

        comments = Table('comments')

        query = PostgreSQLQuery() \
            .from_(comments) \
            .where(comments.source_id == args.add(source_id)) \
            .select(*(comments[field] for field in fields)) \
            .limit(limit) \
            .offset(offset)

        # search for keywords in text
        for keyword in keywords or []:
            arg = args.add(f'%{keyword}%')
            query = query.where(comments.text.like(arg))

        # apply sorting
        if isinstance(sorting, TimestampSorting):
            query = query.orderby(comments.timestamp, order=sorting.order)
        elif isinstance(sorting, FactSorting):
            facts = Table('facts')
            query = query.inner_join(facts).on(Criterion.all([
                facts.comment_id == comments.id,
                facts.label_id == args.add(sorting.label_id)
            ]))
            if sorting.order is UncertaintyOrder:
                query = query.orderby(facts.uncertaintyorder, order=Order.desc)
            else:
                query = query.orderby(facts.confidence, order=sorting.order)

        # filter by document category
        if document_category is not None:
            documents = Table('documents')
            query = query.inner_join(documents).on(documents.id == comments.doc_id) \
                .where(documents.category == args.add(document_category))

        return self._acc.fetch_all(query.get_sql(), args.values)

    def count_by_timestamp_query(
            self,
            granularity: Granularity,
            source_id: int,
            label_id: Optional[int] = None,
            keywords: Optional[List[str]] = None,
    ) -> Iterator[Dict]:
        args = QueryArguments()

        if keywords is None or len(keywords) == 0:
            # optimized query using materialized comments_time_summary view
            summary = Table('comments_time_summary')
            fields = [summary.year, summary.month, summary.day][:granularity.value]

            query = PostgreSQLQuery() \
                .from_(summary) \
                .select(pfn.Cast(pfn.Sum(summary.num), 'bigint').as_('count'), *fields) \
                .where(summary.source_id == args.add(source_id)) \
                .groupby(*fields)

            if label_id is not None:
                query = query.where(summary.label_id == args.add(label_id))
            else:
                query = query.where(summary.label_id.isnull())

        else:
            comments = Table('comments')
            fields = [comments.year, comments.month, comments.day][:granularity.value]

            query = PostgreSQLQuery() \
                .from_(comments) \
                .select(pfn.Count('*').as_('count'), *fields) \
                .where(comments.source_id == args.add(source_id)) \
                .groupby(*fields)

            for keyword in keywords:
                arg = args.add(f'%{keyword}%')
                query = query.where(comments.text.like(arg))

            if label_id is not None:
                facts = Table('facts')
                query = query.inner_join(facts).on(facts.comment_id == comments.id) \
                    .where(facts.label_id == args.add(label_id)) \
                    .where(facts.label == True)

        return self._acc.fetch_all(query.get_sql(), args.values)

    def find_id_by_external_id(self, source_id: int, external_id: str) -> Optional[int]:
        return self._acc.fetch_value(
            'SELECT id FROM comments WHERE source_id = %s AND external_id = %s LIMIT 1',
            (source_id, external_id),
            default=None,
        )

    def find_by_id(self, id_: int, fields: Set[str] = base_comment_fields) -> Dict:
        return self._acc.fetch_one(f'SELECT {", ".join(fields)} FROM comments WHERE id = %s', (id_,))

    def find_all_parents(self, id_: int) -> Iterable[Dict]:
        """Starting with the root comment, find all comments up to and including the queried one"""
        comments = []

        next_id = id_
        while next_id is not None:
            comment = self.find_by_id(next_id, fields=comment_fields(content=True, metadata=True))
            comments.append(comment)
            next_id = comment['parent_comment_id']

        return comments

    def find_first_timestamp_by_source(self, source_id: int) -> Optional[datetime.datetime]:
        return self._acc.fetch_value(
            'SELECT min(timestamp) FROM comments WHERE source_id = %s',
            (source_id,),
            default=None,
        )
