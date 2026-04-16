import base64
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from src import config

logger = logging.getLogger(__name__)

_SALT = b"remily-api-key-encryption-salt"


def _get_fernet() -> Fernet:
    """Derive a Fernet key from API_KEY_ENCRYPTION_KEY using PBKDF2HMAC."""
    master_key = config.API_KEY_ENCRYPTION_KEY
    if not master_key:
        raise RuntimeError(
            "API_KEY_ENCRYPTION_KEY is not set. "
            "Please set it in environment variables to use per-user API key encryption."
        )
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_SALT,
        iterations=480_000,
    )
    derived_key = base64.urlsafe_b64encode(kdf.derive(master_key.encode("utf-8")))
    return Fernet(derived_key)


def encrypt_api_key(plaintext: str) -> str:
    """Encrypt an API key and return the ciphertext as a base64-encoded string."""
    fernet = _get_fernet()
    token = fernet.encrypt(plaintext.encode("utf-8"))
    return base64.urlsafe_b64encode(token).decode("ascii")


def decrypt_api_key(ciphertext: str) -> Optional[str]:
    """Decrypt an API key. Returns None on failure (invalid key, corrupted data, etc.)."""
    try:
        fernet = _get_fernet()
        token = base64.urlsafe_b64decode(ciphertext.encode("ascii"))
        return fernet.decrypt(token).decode("utf-8")
    except (InvalidToken, Exception) as e:
        logger.warning("Failed to decrypt API key: %s", e)
        return None
