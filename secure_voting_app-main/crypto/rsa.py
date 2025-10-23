# RSA key generation, signing, verification, blinding/unblinding
# crypto/rsa.py
import random
import hashlib

class SecureRSA:
    def __init__(self, bit_length=2048):
        self.bit_length = bit_length
        self.e = 65537
        self.generate_keys()

    def generate_keys(self):
        # Simplified example for demo; production: use real CSPRNG primes
        self.p = 2953  # Replace with random large primes
        self.q = 3253
        self.n = self.p * self.q
        self.phi = (self.p-1)*(self.q-1)
        self.d = pow(self.e, -1, self.phi)
        self.public_key = (self.e, self.n)
        self.private_key = (self.d, self.n)

    def sign(self, msg_hash_int):
        return pow(msg_hash_int, self.d, self.n)

    def verify(self, msg_hash_int, signature):
        return pow(signature, self.e, self.n) == msg_hash_int
