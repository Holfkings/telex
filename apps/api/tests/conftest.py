import os
import sys
import pytest

# Ensure apps/api directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Inject a real Fernet key so services/crypto.py doesn't fail closed during tests.
# This key is ephemeral and used only by the test process — never committed as a secret.
if not os.environ.get("TELEX_ENCRYPTION_KEY"):
    from cryptography.fernet import Fernet
    os.environ["TELEX_ENCRYPTION_KEY"] = Fernet.generate_key().decode()
