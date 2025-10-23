# services/voting_authority.py
import os
import secrets
import json
from pathlib import Path
from services.secure_rsa import SecureRSA
from crypto.encryption import VoteEncryption
from db.repositories.token_repository import TokenRepository
from db.repositories.ballot_repository import BallotRepository
from db.repositories.voter_repository import VoterRepository
from db.repositories.encrypted_ballot_repository import EncryptedBallotRepository
from utils.logger import add_log
# from dotenv import load_dotenv
from db.connection import get_conn

# load_dotenv()

class VotingAuthority:
    KEYS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "voting_keys.json")
    ENCRYPTION_KEY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".encryption_key")
    
    def __init__(self, database_connection):
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
        
        # Load or generate encryption key for vote transmission
        self.encryption_key = self._load_or_generate_encryption_key()
        
        self.token_repo = TokenRepository()
        self.ballot_repo = BallotRepository()
        self.voter_repo = VoterRepository()
        self.encrypted_ballot_repo = EncryptedBallotRepository()
        self.encryption = VoteEncryption()
    # self.registered_voters will be set in load_voters_from_db
        self.used_token_hashes = set()
        self.load_voters_from_db()
    
    def _save_keys(self):
        """Save RSA keys to file for persistence"""
        keys_data = {
            'public_key': self.public_key,
            'private_key': self.private_key
        }
        with open(self.KEYS_FILE, 'w') as f:
            json.dump(keys_data, f)
    
    def _load_or_generate_encryption_key(self) -> bytes:
        """
        Load or generate the master encryption key for vote transmission.
        
        Returns:
            bytes: 256-bit encryption key
        """
        if os.path.exists(self.ENCRYPTION_KEY_FILE):
            with open(self.ENCRYPTION_KEY_FILE, 'rb') as f:
                key = f.read()
                if len(key) == VoteEncryption.KEY_SIZE:
                    add_log("Encryption key loaded from file", "info")
                    return key
        
        # Generate new key
        key = VoteEncryption.generate_key()
        with open(self.ENCRYPTION_KEY_FILE, 'wb') as f:
            f.write(key)
        
        # Set restrictive permissions (owner read/write only)
        os.chmod(self.ENCRYPTION_KEY_FILE, 0o600)
        add_log("New encryption key generated and saved", "info")
        return key

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
        """
        Verify token and cast ballot with multi-voting prevention.
        
        Args:
            token_hash: The cryptographic hash of the token
            signature: The RSA signature for the token
            candidate: The candidate the voter is voting for
            
        Returns:
            A ballot ID for confirmation
            
        Raises:
            Exception: If token is invalid, voter not found, or voter has already voted
        """
        # Ensure signature is an integer
        if isinstance(signature, str):
            signature_int = int(signature, 16)
        else:
            signature_int = signature
        
        # Verify the token signature using RSA
        if not self.rsa.verify_hash(token_hash, signature_int, self.public_key):
            raise Exception("Invalid token")
        
        # Get voter_id from token_hash
        voter_id = self.token_repo.get_voter_id_by_token_hash(token_hash)
        if not voter_id:
            raise Exception("Token not found in system")
        
        # CHECK: Prevent multi-voting - voter cannot vote twice
        if self.voter_repo.has_voter_voted(voter_id):
            raise Exception(f"Voter {voter_id} has already cast their vote. One vote per voter is allowed.")
        
        # Add the ballot with the candidate
        self.ballot_repo.add_ballot(candidate)
        
        # Mark voter as voted
        self.voter_repo.mark_voted(voter_id)
        
        # Return a ballot ID for confirmation
        return secrets.token_hex(8)
    
    def verify_token_and_cast_encrypted_ballot(self, token_hash: str, signature: int, 
                                               candidate: str, transmission_envelope: dict):
        """
        Verify token and cast ballot with end-to-end encrypted vote transmission.
        
        This method:
        1. Verifies the RSA token signature
        2. Receives the encrypted vote transmission
        3. Decrypts and validates the vote
        4. Stores the ballot
        5. Prevents multi-voting
        
        Args:
            token_hash: The cryptographic hash of the token
            signature: The RSA signature for the token
            candidate: The candidate the voter is voting for
            transmission_envelope: The encrypted vote transmission
                                  {
                                      'transmission_id': str,
                                      'encrypted_vote': {...},
                                      'envelope_hash': str
                                  }
            
        Returns:
            str: Ballot ID for confirmation
            
        Raises:
            Exception: If token is invalid, decryption fails, or voter has already voted
        """
        try:
            # Ensure signature is an integer
            if isinstance(signature, str):
                signature_int = int(signature, 16)
            else:
                signature_int = signature
            
            # Verify the token signature using RSA
            if not self.rsa.verify_hash(token_hash, signature_int, self.public_key):
                raise Exception("Invalid token signature")
            
            # Get voter_id from token_hash
            voter_id = self.token_repo.get_voter_id_by_token_hash(token_hash)
            if not voter_id:
                raise Exception("Token not found in system")
            
            # CHECK: Prevent multi-voting
            if self.voter_repo.has_voter_voted(voter_id):
                raise Exception(f"Voter {voter_id} has already cast their vote. One vote per voter is allowed.")
            
            # Receive and store encrypted transmission
            transmission_id = transmission_envelope['transmission_id']
            self.encrypted_ballot_repo.add_encrypted_ballot(
                transmission_id,
                transmission_envelope['encrypted_vote']['nonce'],
                transmission_envelope['encrypted_vote']['ciphertext'],
                transmission_envelope['encrypted_vote']['tag'],
                transmission_envelope['envelope_hash']
            )
            
            # Verify envelope integrity
            computed_hash = VoteEncryption.compute_envelope_hash(transmission_envelope['encrypted_vote'])
            if computed_hash != transmission_envelope['envelope_hash']:
                raise Exception("Envelope integrity verification failed")
            
            # Decrypt vote
            decrypted_vote = self.encryption.decrypt_vote(
                transmission_envelope['encrypted_vote'],
                self.encryption_key
            )
            
            # Validate decrypted vote contains expected candidate
            if decrypted_vote.get('candidate') != candidate:
                raise Exception("Decrypted candidate doesn't match transmitted candidate")
            
            # Add the ballot with the candidate
            self.ballot_repo.add_ballot(candidate)
            
            # Mark voter as voted
            self.voter_repo.mark_voted(voter_id)
            
            # Log successful encrypted vote processing
            add_log(
                f"Encrypted vote processed: voter={voter_id}, "
                f"transmission_id={transmission_id}, candidate={candidate}",
                "info"
            )
            
            # Return ballot ID
            ballot_id = secrets.token_hex(8)
            return ballot_id
            
        except Exception as e:
            add_log(f"Error processing encrypted ballot: {str(e)}", "error")
            raise

    def get_public_key(self):
        return self.public_key
    
    def get_encryption_key(self) -> bytes:
        """Get the master encryption key for vote transmission."""
        return self.encryption_key
