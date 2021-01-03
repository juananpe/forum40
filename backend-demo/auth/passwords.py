import secrets
from dataclasses import dataclass

import hashlib
from base64 import b64encode, b64decode
from typing import Tuple


@dataclass
class DifficultyParameters:
    n: int
    r: int
    p: int


SALT_N_BYTES = 16
KEY_LENGTH = 32
MAXMEM = 64 * 1024**2
DEFAULT_PARAMS = DifficultyParameters(n=1 << 15, r=8, p=1)
ENCODING_SEPARATOR = '$'


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(SALT_N_BYTES)
    hash = compute_hash(password, salt, params=DEFAULT_PARAMS)
    return encode(hash, salt, params=DEFAULT_PARAMS)


def compare_hash_and_password(hashed_password: str, password: str) -> bool:
    hash, salt, params = decode(hashed_password)
    test_hash = compute_hash(password, salt, params)
    return secrets.compare_digest(hash, test_hash)


def compute_hash(password: str, salt: bytes, params: DifficultyParameters) -> bytes:
    return hashlib.scrypt(password.encode('utf8'), salt=salt, n=params.n, r=params.r, p=params.p, maxmem=MAXMEM, dklen=KEY_LENGTH)


def encode(hash: bytes, salt: bytes, params: DifficultyParameters) -> str:
    return ENCODING_SEPARATOR.join([
        str(params.n), str(params.r), str(params.p),
        b64encode(salt).decode('utf8'), b64encode(hash).decode('utf8'),
    ])


def decode(s: str) -> Tuple[bytes, bytes, DifficultyParameters]:
    n, r, p, salt_b64, hash_b64 = s.split(ENCODING_SEPARATOR)
    return (
        b64decode(hash_b64.encode('utf8')),
        b64decode(salt_b64.encode('utf8')),
        DifficultyParameters(n=int(n), r=int(r), p=int(p)),
    )

