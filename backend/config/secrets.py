from pathlib import Path


class Secrets:
    def __init__(self, base_path: Path = Path('/run/secrets/')):
        self.base_path = base_path
        self._cache = {}

    def __getitem__(self, item) -> bytes:
        if not isinstance(item, str):
            raise TypeError(f'Invalid secret key type {type(item)}')

        if item not in self._cache:
            secret_file = self.base_path / item
            if not secret_file.exists():
                raise KeyError('Secret does not exist')

            with secret_file.open('rb') as f:
                self._cache[item] = f.read()

        return self._cache[item]


secrets = Secrets()
