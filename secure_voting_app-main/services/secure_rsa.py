import secrets
from hashlib import sha256

class SecureRSA:
    """
    Production-ready RSA implementation with blind signature support.
    """

    def __init__(self, bit_length: int = 2048):
        self.bit_length = bit_length
        self.public_key = None
        self.private_key = None

    # -------------------
    # Math utilities
    # -------------------
    @staticmethod
    def gcd(a: int, b: int) -> int:
        while b != 0:
            a, b = b, a % b
        return a

    @staticmethod
    def mod_inverse(a: int, m: int) -> int:
        old_r, r = a, m
        old_s, s = 1, 0
        while r != 0:
            quotient = old_r // r
            old_r, r = r, old_r - quotient * r
            old_s, s = s, old_s - quotient * s
        if old_s < 0:
            old_s += m
        return old_s

    @staticmethod
    def mod_pow(base: int, exp: int, mod: int) -> int:
        result = 1
        base = base % mod
        while exp > 0:
            if exp % 2 == 1:
                result = (result * base) % mod
            exp = exp >> 1
            base = (base * base) % mod
        return result

    # -------------------
    # Prime generation
    # -------------------
    @staticmethod
    def is_prime(n: int, k: int = 40) -> bool:
        """Miller-Rabin primality test."""
        if n in (2, 3):
            return True
        if n < 2 or n % 2 == 0:
            return False
        r, d = 0, n - 1
        while d % 2 == 0:
            d //= 2
            r += 1
        for _ in range(k):
            a = secrets.randbelow(n - 3) + 2
            x = pow(a, d, n)
            if x == 1 or x == n - 1:
                continue
            for _ in range(r - 1):
                x = pow(x, 2, n)
                if x == n - 1:
                    break
            else:
                return False
        return True

    def generate_prime(self, bits: int) -> int:
        while True:
            candidate = secrets.randbits(bits) | 1
            candidate |= (1 << bits - 1)  # Ensure bit length
            if self.is_prime(candidate):
                return candidate

    # -------------------
    # Key generation
    # -------------------
    def generate_keys(self):
        p = self.generate_prime(self.bit_length // 2)
        q = self.generate_prime(self.bit_length // 2)
        n = p * q
        phi = (p - 1) * (q - 1)
        e = 65537
        while self.gcd(e, phi) != 1:
            e += 2
        d = self.mod_inverse(e, phi)
        self.public_key = {"n": n, "e": e}
        self.private_key = {"n": n, "d": d}
        return self.public_key, self.private_key

    # -------------------
    # Signing & verification
    # -------------------
    @staticmethod
    def hash_message(msg: str) -> int:
        return int(sha256(msg.encode()).hexdigest(), 16)

    def sign(self, msg: str) -> int:
        h = self.hash_message(msg)
        return self.mod_pow(h, self.private_key["d"], self.private_key["n"])

    def verify(self, msg: str, signature: int) -> bool:
        h = self.hash_message(msg)
        decrypted = self.mod_pow(signature, self.public_key["e"], self.public_key["n"])
        return h == decrypted
    
    def verify_hash(self, hash_hex: str, signature: int, public_key: dict) -> bool:
        """
        Verifies that signature^e mod n equals the hash value.
        """
        e = public_key["e"]
        n = public_key["n"]
        h = int(hash_hex, 16)
        return pow(signature, e, n) == h
    
    # -------------------
    # Blind signatures
    # -------------------
    def blind(self, msg: str):
        n = self.public_key["n"]
        e = self.public_key["e"]
        h = self.hash_message(msg)
        while True:
            r = secrets.randbelow(n - 2) + 2
            if self.gcd(r, n) == 1:
                break
        blinded = (h * pow(r, e, n)) % n
        return blinded, r

    def unblind(self, blinded_sig: int, r: int):
        n = self.public_key["n"]
        r_inv = self.mod_inverse(r, n)
        return (blinded_sig * r_inv) % n

    def sign_blind(self, blinded: int) -> int:
        return self.mod_pow(blinded, self.private_key["d"], self.private_key["n"])
