from typing import Optional, Dict

from auth.passwords import compare_hash_and_password
from db import with_database, Database


@with_database
def login(db: Database, user_name: str, password: str) -> Optional[Dict]:
    user = db.users.find_by_name(user_name)
    if user is None:
        return None

    password_correct = compare_hash_and_password(user['password'], password)
    if not password_correct:
        return None

    return user
