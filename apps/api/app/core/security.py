"""
Password hashing.

argon2 (not bcrypt, never plaintext) per the roadmap's explicit
Stage 2 requirement. argon2 is the current recommended algorithm for
new applications — it won the Password Hashing Competition and is
designed specifically to resist GPU/ASIC-accelerated cracking attempts
better than older algorithms.

PasswordHasher() with default parameters is intentional here — the
defaults are already tuned by the argon2-cffi maintainers to current
security recommendations. Don't hand-tune time_cost/memory_cost
without a specific, documented reason.
"""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher()


def hash_password(plain_password: str) -> str:
    return _hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        _hasher.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False
