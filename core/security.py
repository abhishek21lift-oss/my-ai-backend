import hashlib
import hmac
import secrets


def generate_api_key() -> tuple[str, str, str]:
    """
    Returns (raw_key, key_hash, key_prefix).
    raw_key   : shown once to user — e.g. "sk-abc123..."
    key_hash  : SHA-256 hex digest — stored in DB, raw key never stored
    key_prefix: first 10 chars of raw_key — shown in UI for identification
    """
    token = secrets.token_hex(32)  # 64 random hex chars
    raw_key = f"sk-{token}"
    key_prefix = raw_key[:10]
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, key_hash, key_prefix


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    computed = hash_api_key(raw_key)
    return hmac.compare_digest(computed, stored_hash)
