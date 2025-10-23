# services/voter_client.py
import secrets
from services.secure_rsa import SecureRSA
from services.voting_authority import VotingAuthority
from db.repositories.token_repository import TokenRepository
from db.repositories.voter_repository import VoterRepository
from utils.crypto import sha256_hex

class VoterClient:
    def __init__(self, authority: VotingAuthority):
        self.authority = authority
        self.token_repo = TokenRepository()
        self.voter_repo = VoterRepository()
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
        """
        Cast a vote with multi-voting prevention.
        
        Args:
            token_hash: The token hash for the voter
            signature: The RSA signature
            candidate: The selected candidate
            
        Returns:
            The ballot ID if successful
            
        Raises:
            Exception: If voter has already voted or other validation fails
        """
        # Get voter_id from token
        voter_id = self.token_repo.get_voter_id_by_token_hash(token_hash)
        if not voter_id:
            raise Exception("Token not found")
        
        # Check if voter has already voted
        if self.voter_repo.has_voter_voted(voter_id):
            raise Exception(f"Voter has already cast their vote. Only one vote per voter is permitted.")
        
        # Proceed with vote casting via authority
        return self.authority.verify_token_and_cast_ballot(token_hash, signature, candidate)
