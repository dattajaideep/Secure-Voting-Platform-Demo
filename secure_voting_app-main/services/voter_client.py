# services/voter_client.py
import secrets
from datetime import datetime
from services.secure_rsa import SecureRSA
from services.voting_authority import VotingAuthority
from services.vote_transmission import VoteTransmissionService
from db.repositories.token_repository import TokenRepository
from db.repositories.voter_repository import VoterRepository
from utils.crypto import sha256_hex
from utils.logger import add_log

class VoterClient:
    def __init__(self, authority: VotingAuthority, transmission_service: VoteTransmissionService = None):
        self.authority = authority
        self.token_repo = TokenRepository()
        self.voter_repo = VoterRepository()
        self.public_key = authority.get_public_key()
        self.rsa = SecureRSA()
        # Initialize transmission service for encrypted vote transmission
        self.transmission_service = transmission_service or VoteTransmissionService()
        self.transmission_service.set_master_encryption_key(authority.get_encryption_key())

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
        Cast a vote with end-to-end encryption and multi-voting prevention.
        
        Args:
            token_hash: The token hash for the voter
            signature: The RSA signature
            candidate: The selected candidate
            
        Returns:
            dict: Result containing ballot_id and transmission_id
                 {
                     'ballot_id': str,
                     'transmission_id': str,
                     'status': 'success',
                     'encrypted': True
                 }
            
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
        
        # Prepare vote data for encryption
        vote_data = {
            'voter_id': voter_id,
            'candidate': candidate,
            'token_hash': token_hash,
            'signature': str(signature) if isinstance(signature, int) else signature,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Encrypt vote for transmission
        transmission_envelope = self.transmission_service.prepare_vote_for_transmission(vote_data)
        transmission_id = transmission_envelope['transmission_id']
        
        # Proceed with vote casting via authority (decryption + validation happens on server side)
        ballot_id = self.authority.verify_token_and_cast_encrypted_ballot(
            token_hash, signature, candidate, transmission_envelope
        )
        
        add_log(f"Encrypted vote transmitted: voter={voter_id}, transmission_id={transmission_id}", "info")
        
        return {
            'ballot_id': ballot_id,
            'transmission_id': transmission_id,
            'status': 'success',
            'encrypted': True
        }
