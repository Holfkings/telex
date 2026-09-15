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

Security posture:
  - TELEX_ENCRYPTION_KEY is REQUIRED in all non-test environments.
  - There is NO deterministic development fallback. A missing key is a hard
    startup failure unless `TELEX_TEST_MODE=1` is explicitly set (used only by
    the automated test suite which injects a generated key via env vars).
  - This prevents accidental exposure if the app is deployed without the key.
"""
import logging
import os

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

_ENCRYPTION_KEY_ENV = "TELEX_ENCRYPTION_KEY"
# Only set by the test suite (conftest.py / pytest fixtures). Never set in production.
_TEST_MODE_ENV = "TELEX_TEST_MODE"


def _get_master_key() -> bytes:
    """
    Retrieve the Fernet master key.

    Current implementation: reads TELEX_ENCRYPTION_KEY from the environment.
    To swap in a KMS: replace this function body. All call sites are unchanged.

    Raises RuntimeError if the key is absent (unless TELEX_TEST_MODE=1).
    """
    raw = os.environ.get(_ENCRYPTION_KEY_ENV, "").strip()
    if not raw:
        # Fail closed — no silent fallback.
        # TELEX_TEST_MODE=1 is only set by the automated test suite which
        # injects a real generated key via conftest.py/environment setup.
        # This branch should never be reached in production or staging.
        test_mode = os.environ.get(_TEST_MODE_ENV, "").strip() == "1"
        if test_mode:
            # Tests must also supply a real key; this is just a guard message.
            raise RuntimeError(
                f"{_ENCRYPTION_KEY_ENV} must be set in test mode. "
                "Add it to conftest.py: "
                "os.environ['TELEX_ENCRYPTION_KEY'] = Fernet.generate_key().decode()"
            )
        raise RuntimeError(
            f"Startup blocked: {_ENCRYPTION_KEY_ENV} is not set. "
            "Generate one with: "
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )

    try:
        key_bytes = raw.encode() if isinstance(raw, str) else raw
        # Validate by constructing Fernet — it raises ValueError on bad keys.
        Fernet(key_bytes)
        return key_bytes
    except Exception as exc:
        raise RuntimeError(
            f"{_ENCRYPTION_KEY_ENV} is not a valid Fernet key: {exc}. "
            "Generate one with: "
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
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
    except InvalidToken:
        logger.error("crypto.decrypt_key: InvalidToken — key may have rotated or ciphertext is corrupt")
        raise
