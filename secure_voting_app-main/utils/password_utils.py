"""
Password Utilities Module

Handles password hashing, verification, and encoding/decoding with bcrypt.
Implements secure password salting to protect against rainbow table and 
brute-force attacks. All passwords are hashed with randomly generated salts
and encoded to base64 for database storage.
"""

import bcrypt
import secrets
import base64

def generate_salt() -> bytes:
    """Generate a random salt for password hashing"""
    return bcrypt.gensalt()

def hash_password(password: str, salt: bytes = None) -> tuple[bytes, bytes]:
    """
    Hash a password using bcrypt with a random salt or provided salt

    Args:
        password: The password to hash
        salt: Optional salt to use, if None a new salt will be generated

    Returns:
        tuple: (hashed_password, salt)
    """
    if not salt:
        salt = generate_salt()

    # Convert password to bytes if it's not already
    if isinstance(password, str):
        password = password.encode('utf-8')

    hashed = bcrypt.hashpw(password, salt)
    return hashed, salt

def verify_password(password: str, hashed_password: bytes, salt: bytes) -> bool:
    """
    Verify a password against its hash

    Args:
        password: The password to verify
        hashed_password: The stored hash to verify against
        salt: The salt used in hashing

    Returns:
        bool: True if password matches, False otherwise
    """
    if isinstance(password, str):
        password = password.encode('utf-8')

    # Verify the password
    return bcrypt.checkpw(password, hashed_password)

def encode_hash_salt(hashed: bytes, salt: bytes) -> tuple[str, str]:
    """
    Encode hashed password and salt to base64 strings for storage

    Args:
        hashed: The hashed password bytes
        salt: The salt bytes

    Returns:
        tuple: (encoded_hash, encoded_salt)
    """
    return (
        base64.b64encode(hashed).decode('utf-8'),
        base64.b64encode(salt).decode('utf-8')
    )

def decode_hash_salt(encoded_hash: str, encoded_salt: str) -> tuple[bytes, bytes]:
    """
    Decode base64 stored hash and salt back to bytes

    Args:
        encoded_hash: The base64 encoded hash string
        encoded_salt: The base64 encoded salt string

    Returns:
        tuple: (hash_bytes, salt_bytes)
    """
    return (
        base64.b64decode(encoded_hash.encode('utf-8')),
        base64.b64decode(encoded_salt.encode('utf-8'))
    )