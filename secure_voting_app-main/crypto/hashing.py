# SHA-256 hashing utilities with encryption key support
# crypto/hashing.py
import hashlib
import hmac
import os
import base64
import binascii
from dotenv import load_dotenv

# Load environment variables from a local .env for development only
load_dotenv()

# Application secrets: prefer CI-provided environment values. We accept either
# raw/text keys or base64-encoded binary via ENCRYPTION_KEY_B64 and SALT_B64.
SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')

# Support ENCRYPTION_KEY_B64 (base64) or ENCRYPTION_KEY (hex or raw)
_enc_b64 = os.getenv('ENCRYPTION_KEY_B64')
if _enc_b64:
    try:
        ENCRYPTION_KEY_BYTES = base64.b64decode(_enc_b64)
    except (binascii.Error, TypeError):
        # fallback if provided value is not proper base64
        ENCRYPTION_KEY_BYTES = _enc_b64.encode()
else:
    _enc = os.getenv('ENCRYPTION_KEY')
    if _enc:
        # try hex decode (common), otherwise use raw bytes
        try:
            ENCRYPTION_KEY_BYTES = binascii.unhexlify(_enc)
        except (binascii.Error, TypeError):
            ENCRYPTION_KEY_BYTES = _enc.encode()
    else:
        ENCRYPTION_KEY_BYTES = None

# Support SALT_B64 (base64) or SALT_FILE fallback
_salt_b64 = os.getenv('SALT_B64')
if _salt_b64:
    try:
        SALT_BYTES = base64.b64decode(_salt_b64)
    except (binascii.Error, TypeError):
        SALT_BYTES = _salt_b64.encode()
else:
    SALT_BYTES = None

SALT_FILE = os.getenv('SALT_FILE', '.salt')

def get_salt():
    """Return salt bytes. Prefer SALT_B64 env, otherwise load or create SALT_FILE."""
    if SALT_BYTES is not None:
        return SALT_BYTES
    if os.path.exists(SALT_FILE):
        with open(SALT_FILE, 'rb') as f:
            return f.read()
    else:
        # Create default salt if doesn't exist (development only)
        import secrets
        salt = secrets.token_bytes(32)
        with open(SALT_FILE, 'wb') as f:
            f.write(salt)
        return salt

def sha256_hex(message: str) -> str:
    """Simple SHA-256 hash"""
    return hashlib.sha256(message.encode()).hexdigest()

def hash_password(password: str) -> str:
    """Hash password using SECRET_KEY and salt"""
    salt = get_salt()
    return hmac.new(
        SECRET_KEY.encode(),
        password.encode() + salt,
        hashlib.sha256
    ).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed

def encrypt_data(data: str) -> str:
    """Encrypt data using ENCRYPTION_KEY"""
    from cryptography.fernet import Fernet
    # Derive a 32-byte key from the configured ENCRYPTION_KEY_BYTES or ENCRYPTION_KEY
    if ENCRYPTION_KEY_BYTES is not None:
        raw = hashlib.sha256(ENCRYPTION_KEY_BYTES).digest()
    else:
        # fallback to a default (not secure) if nothing configured
        raw = hashlib.sha256(b'default_encryption_key').digest()
    key = base64.urlsafe_b64encode(raw)
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    """Decrypt data using ENCRYPTION_KEY"""
    from cryptography.fernet import Fernet
    if ENCRYPTION_KEY_BYTES is not None:
        raw = hashlib.sha256(ENCRYPTION_KEY_BYTES).digest()
    else:
        raw = hashlib.sha256(b'default_encryption_key').digest()
    key = base64.urlsafe_b64encode(raw)
    f = Fernet(key)
    return f.decrypt(encrypted_data.encode()).decode()
