# services/voting_authority.py
import os
import secrets
from services.secure_rsa import SecureRSA
from db.repositories.token_repository import TokenRepository
from db.repositories.ballot_repository import BallotRepository
# from dotenv import load_dotenv
from db.connection import get_conn

# load_dotenv()

class VotingAuthority:
    def __init__(self,database_connection):
        self.db = database_connection
        self.rsa = SecureRSA(1024)  # Demo: Production should use 2048+
        public_key, private_key = self.rsa.generate_keys()
        self.public_key = public_key
        self.private_key = private_key
        self.token_repo = TokenRepository()
        self.ballot_repo = BallotRepository()
    # self.registered_voters will be set in load_voters_from_db
        self.used_token_hashes = set()
        self.load_voters_from_db()

    def load_voters_from_db(self):
        # Assuming you have a voters table with voter_id
        cursor = self.db.cursor()
        cursor.execute("SELECT voter_id FROM voters")
        rows = cursor.fetchall()
        self.registered_voters = set(row['voter_id'] for row in rows)
    
    def register_voter(self, voter_id: str):
        self.registered_voters.add(voter_id)

    def issue_blind_signature(self, blinded_hash: int, voter_id: str):
        if voter_id not in self.registered_voters:
            raise Exception("Voter not registered")
        return self.rsa.mod_pow(blinded_hash, self.private_key["d"], self.private_key["n"])

    def verify_token_and_cast_ballot(self, token_hash: str, signature: int, candidate: str):
        signature_int = int(signature, 16) if isinstance(signature, str) else signature
        if not self.rsa.verify_hash(token_hash, signature_int, self.public_key):
            raise Exception("Invalid token")
        ballot_id = secrets.token_hex(8)
        self.ballot_repo.add_ballot(ballot_id, candidate, token_hash)
        return ballot_id

    def get_public_key(self):
        return self.public_key
