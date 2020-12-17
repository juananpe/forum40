from collections import defaultdict

from typing import TypeVar, Iterable, Dict

T = TypeVar('T')


def slice_dicts(items: Iterable[Dict[str, T]], mapping: Dict[str, str]) -> Dict[str, T]:
    result = defaultdict(list)
    for item in items:
        for out_key, in_key in mapping.items():
            result[out_key].append(item[in_key])

    return dict(result)
