from db.accessor import DatabaseAccessor


class BaseRepository:
    def __init__(self, accessor: DatabaseAccessor):
        self._acc = accessor
