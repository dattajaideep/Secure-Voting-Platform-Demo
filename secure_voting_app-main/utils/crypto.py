# utils/crypto.py
import hashlib

def sha256_hex(msg: str):
    return hashlib.sha256(msg.encode()).hexdigest()
