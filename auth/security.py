# =============================================================
# auth/security.py
# TalentMatch AI - Password Hashing (stdlib only, no third-party auth libs)
# =============================================================
import hashlib
import secrets

_ALGORITHM = "sha256"
_ITERATIONS = 260_000
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    """
    Derives a salted PBKDF2-HMAC-SHA256 hash for the given plaintext password.

    Returns:
        str: "salt$iterations$hexdigest", so the iteration count can be
             increased later without invalidating stored hash format.
    """
    salt = secrets.token_hex(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        _ALGORITHM, password.encode("utf-8"), bytes.fromhex(salt), _ITERATIONS
    )
    return f"{salt}${_ITERATIONS}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verifies a plaintext password against a stored "salt$iterations$hexdigest" hash.

    Returns:
        bool: True if the password matches, False otherwise (including on any
              malformed stored hash, which is treated as a verification failure).
    """
    try:
        salt, iterations_str, hex_digest = password_hash.split("$")
        iterations = int(iterations_str)
    except (ValueError, AttributeError):
        return False

    candidate_digest = hashlib.pbkdf2_hmac(
        _ALGORITHM, password.encode("utf-8"), bytes.fromhex(salt), iterations
    )
    return secrets.compare_digest(candidate_digest.hex(), hex_digest)
