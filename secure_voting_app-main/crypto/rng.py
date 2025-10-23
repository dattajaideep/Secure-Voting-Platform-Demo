# Cryptographically secure random number generator utilities
# crypto/rng.py
import secrets

def get_random_hex(n_bytes=32):
    return secrets.token_hex(n_bytes)
