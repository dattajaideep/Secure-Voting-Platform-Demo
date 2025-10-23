# SHA-256 hashing utilities with encryption key support
# crypto/hashing.py
import hashlib
import hmac
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'default_encryption_key')
SALT_FILE = os.getenv('SALT_FILE', '.salt')

def get_salt():
    """Load salt from file"""
    if os.path.exists(SALT_FILE):
        with open(SALT_FILE, 'rb') as f:
            return f.read()
    else:
        # Create default salt if doesn't exist
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
    import base64
    
    # Generate a proper key from ENCRYPTION_KEY
    key = base64.urlsafe_b64encode(
        hashlib.sha256(ENCRYPTION_KEY.encode()).digest()
    )
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    """Decrypt data using ENCRYPTION_KEY"""
    from cryptography.fernet import Fernet
    import base64
    
    key = base64.urlsafe_b64encode(
        hashlib.sha256(ENCRYPTION_KEY.encode()).digest()
    )
    f = Fernet(key)
    return f.decrypt(encrypted_data.encode()).decode()
