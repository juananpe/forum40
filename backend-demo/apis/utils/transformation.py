from typing import TypeVar, Iterable, Dict

T = TypeVar('T')


def slice_dicts(items: Iterable[Dict[str, T]], mapping: Dict[str, str]) -> Dict[str, T]:
    return {out_key: [item[in_key] for item in items] for out_key, in_key in mapping.items()}
