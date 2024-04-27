import hashlib
import string

from random import SystemRandom


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    if salt is None:
        random = SystemRandom()
        salt = "".join(random.choices(string.ascii_lowercase, k=16))

    salted_password = password + salt
    password_hash = hashlib.sha256(salted_password.encode()).hexdigest()
    return password_hash, salt


def validate_password(password: str, password_hash: str, salt: str) -> bool:
    return hash_password(password, salt)[0] == password_hash
