# SHA-256 hashing utilities
# crypto/hashing.py
import hashlib

def sha256_hex(message: str) -> str:
    return hashlib.sha256(message.encode()).hexdigest()
