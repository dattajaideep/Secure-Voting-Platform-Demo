# services/voting_authority.py
import os
import secrets
import json
from pathlib import Path
from services.secure_rsa import SecureRSA
from db.repositories.token_repository import TokenRepository
from db.repositories.ballot_repository import BallotRepository
# from dotenv import load_dotenv
from db.connection import get_conn

# load_dotenv()

class VotingAuthority:
    KEYS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "voting_keys.json")
    
    def __init__(self,database_connection):
        self.db = database_connection
        self.rsa = SecureRSA(1024)  # Demo: Production should use 2048+
        
        # Load or generate RSA keys
        if os.path.exists(self.KEYS_FILE):
            with open(self.KEYS_FILE, 'r') as f:
                keys_data = json.load(f)
                self.public_key = keys_data['public_key']
                self.private_key = keys_data['private_key']
        else:
            public_key, private_key = self.rsa.generate_keys()
            self.public_key = public_key
            self.private_key = private_key
            # Save keys for future use
            self._save_keys()
        
        self.token_repo = TokenRepository()
        self.ballot_repo = BallotRepository()
    # self.registered_voters will be set in load_voters_from_db
        self.used_token_hashes = set()
        self.load_voters_from_db()
    
    def _save_keys(self):
        """Save keys to file for persistence"""
        keys_data = {
            'public_key': self.public_key,
            'private_key': self.private_key
        }
        with open(self.KEYS_FILE, 'w') as f:
            json.dump(keys_data, f)

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
        # Ensure signature is an integer
        if isinstance(signature, str):
            signature_int = int(signature, 16)
        else:
            signature_int = signature
        
        # Verify the token signature using RSA
        if not self.rsa.verify_hash(token_hash, signature_int, self.public_key):
            raise Exception("Invalid token")
        
        # Add the ballot with the candidate
        self.ballot_repo.add_ballot(candidate)
        # Return a ballot ID for confirmation
        return secrets.token_hex(8)

    def get_public_key(self):
        return self.public_key
