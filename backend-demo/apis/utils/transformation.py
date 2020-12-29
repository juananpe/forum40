import itertools
from collections import defaultdict

from typing import TypeVar, Dict, Optional, Iterable

T = TypeVar('T')


def slice_dicts(items: Iterable[Dict[str, T]], mapping: Optional[Dict[str, str]] = None) -> Dict[str, T]:
    items = iter(items)

    if mapping is None:
        first_item = next(items)
        mapping = {key: key for key in first_item.keys()}
        items = itertools.chain([first_item], items)

    result = defaultdict(list)
    for item in items:
        for out_key, in_key in mapping.items():
            result[out_key].append(item[in_key])

    return dict(result)
