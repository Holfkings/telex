"""
crypto.py — BYOK key encryption/decryption.

Uses Fernet symmetric encryption (cryptography library). The master key is
retrieved via `_get_master_key()` — a single, swappable function. Swap this
one function to integrate a proper KMS (AWS Secrets Manager, GCP Secret
Manager, HashiCorp Vault) without touching any call site.

Master key rules:
  - Must be a URL-safe base64-encoded 32-byte value (output of Fernet.generate_key()).
  - Must come from an environment variable TELEX_ENCRYPTION_KEY — never from a
    plaintext .env value committed to the repo.
  - Is never logged.
"""
import base64
import logging
import os

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

_ENCRYPTION_KEY_ENV = "TELEX_ENCRYPTION_KEY"


def _get_master_key() -> bytes:
    """
    Retrieve the Fernet master key.

    Current implementation: reads TELEX_ENCRYPTION_KEY from the environment.
    To swap in a KMS: replace this function body. All call sites are unchanged.

    Raises RuntimeError if the key is absent or malformed.
    """
    raw = os.environ.get(_ENCRYPTION_KEY_ENV, "")
    if not raw:
        # Development fallback — deterministic, never used in production.
        _env = os.environ.get("ENVIRONMENT", "development").strip().lower()
        _render = bool(os.environ.get("RENDER"))
        if _env == "production" or _render:
            raise RuntimeError(
                f"Production startup blocked: {_ENCRYPTION_KEY_ENV} is not set. "
                "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        # Local dev — derive a fixed key from a constant so tests don't fail.
        # This key is NOT secret and is only used when ENVIRONMENT != production.
        _dev_seed = b"telex-dev-encryption-key-32-bytes!!"[:32]
        raw = base64.urlsafe_b64encode(_dev_seed).decode()
        logger.debug("crypto: using ephemeral development encryption key (not for production)")
    try:
        key_bytes = raw.encode() if isinstance(raw, str) else raw
        # Validate by constructing Fernet — it raises ValueError on bad keys.
        Fernet(key_bytes)
        return key_bytes
    except Exception as exc:
        raise RuntimeError(
            f"{_ENCRYPTION_KEY_ENV} is not a valid Fernet key: {exc}. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        ) from exc


def encrypt_key(plaintext: str) -> str:
    """
    Encrypt a plaintext API key and return a Fernet ciphertext string.
    The ciphertext is safe to store in the database.
    """
    master_key = _get_master_key()
    ciphertext = Fernet(master_key).encrypt(plaintext.encode()).decode()
    return ciphertext


def decrypt_key(ciphertext: str) -> str:
    """
    Decrypt a Fernet ciphertext back to the plaintext API key.

    Raises:
        cryptography.fernet.InvalidToken — if the ciphertext is corrupt or
            the master key has rotated since encryption.
    """
    master_key = _get_master_key()
    try:
        return Fernet(master_key).decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        logger.error("crypto.decrypt_key: InvalidToken — key may have rotated or ciphertext is corrupt")
        raise
