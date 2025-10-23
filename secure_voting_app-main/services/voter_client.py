# services/voter_client.py
import secrets
from services.secure_rsa import SecureRSA
from services.voting_authority import VotingAuthority
from db.repositories.token_repository import TokenRepository
from utils.crypto import sha256_hex

class VoterClient:
    def __init__(self, authority: VotingAuthority):
        self.authority = authority
        self.token_repo = TokenRepository()
        self.public_key = authority.get_public_key()
        self.rsa = SecureRSA()

    def create_blind_token(self, voter_id: str):
        token = secrets.token_hex(16)
        token_hash = sha256_hex(token)
        r = secrets.randbelow(self.public_key["n"] - 2) + 2
        h = int(token_hash, 16)
        blinded_hash = (h * self.rsa.mod_pow(r, self.public_key["e"], self.public_key["n"])) % self.public_key["n"]
        blinded_sig = self.authority.issue_blind_signature(blinded_hash, voter_id)
        signature = (blinded_sig * self.rsa.mod_inverse(r, self.public_key["n"])) % self.public_key["n"]
        self.token_repo.add_token(voter_id, token_hash, hex(signature))
        return token_hash, hex(signature)

    def cast_vote(self, token_hash: str, signature: int, candidate: str):
        return self.authority.verify_token_and_cast_ballot(token_hash, signature, candidate)
