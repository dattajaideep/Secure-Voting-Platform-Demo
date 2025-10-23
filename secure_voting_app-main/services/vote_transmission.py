# services/vote_transmission.py
"""
Vote Transmission Service with End-to-End Encryption

Handles the encryption, transmission, and decryption of votes
using AES-256-GCM authenticated encryption.

Workflow:
1. Voter encrypts vote before sending
2. Vote is transmitted securely
3. Authority receives and verifies integrity
4. Authority decrypts vote for processing
"""

import json
import secrets
from datetime import datetime
from crypto.encryption import VoteEncryption, TransmissionChannel
from db.repositories.encrypted_ballot_repository import EncryptedBallotRepository
from utils.logger import add_log


class VoteTransmissionService:
    """
    Manages secure end-to-end encrypted vote transmission.
    
    Features:
    - AES-256-GCM encryption for all votes in transit
    - Authenticated encryption with integrity verification
    - Transmission tracking and receipt acknowledgment
    - Support for key rotation
    """
    
    def __init__(self):
        """Initialize the vote transmission service."""
        self.encryption = VoteEncryption()
        self.ballot_repo = EncryptedBallotRepository()
        self.channels = {}  # Track active transmission channels
        self.master_key = None  # Will be set by authority
    
    def set_master_encryption_key(self, key: bytes):
        """
        Set the master encryption key for all transmissions.
        
        Args:
            key: 256-bit encryption key (32 bytes)
            
        Raises:
            ValueError: If key size is invalid
        """
        if len(key) != VoteEncryption.KEY_SIZE:
            raise ValueError(f"Key must be {VoteEncryption.KEY_SIZE} bytes, got {len(key)}")
        self.master_key = key
        add_log("Master encryption key set for vote transmission", "info")
    
    def create_transmission_channel(self, channel_id: str = None) -> str:
        """
        Create a new transmission channel for vote encryption.
        
        Args:
            channel_id: Optional custom channel ID (generated if not provided)
            
        Returns:
            str: The channel ID
        """
        if channel_id is None:
            channel_id = f"channel_{secrets.token_hex(8)}"
        
        channel = TransmissionChannel(channel_id)
        self.channels[channel_id] = channel
        
        add_log(f"Transmission channel created: {channel_id}", "info")
        return channel_id
    
    def get_transmission_channel(self, channel_id: str) -> TransmissionChannel:
        """
        Retrieve a transmission channel.
        
        Args:
            channel_id: The channel identifier
            
        Returns:
            TransmissionChannel: The channel object
            
        Raises:
            KeyError: If channel doesn't exist
        """
        if channel_id not in self.channels:
            raise KeyError(f"Transmission channel not found: {channel_id}")
        return self.channels[channel_id]
    
    def prepare_vote_for_transmission(self, vote_data: dict, 
                                     channel_id: str = None) -> dict:
        """
        Prepare a vote for secure transmission by encrypting it.
        
        Args:
            vote_data: Vote information
                      {
                          'voter_id': str,
                          'candidate': str,
                          'token_hash': str,
                          'timestamp': str (ISO format)
                      }
            channel_id: Optional channel ID (uses default if not provided)
            
        Returns:
            dict: Transmission envelope ready to send
                 {
                     'transmission_id': str,
                     'channel_id': str,
                     'encrypted_vote': {
                         'nonce': str,
                         'ciphertext': str,
                         'tag': str,
                         'algorithm': str
                     },
                     'envelope_hash': str,
                     'prepared_at': str
                 }
                 
        Raises:
            ValueError: If no key is set or channel not found
        """
        if self.master_key is None:
            raise ValueError("Master encryption key not set. Call set_master_encryption_key() first.")
        
        if channel_id is None:
            # Use default channel or create one
            if "default" not in self.channels:
                self.create_transmission_channel("default")
            channel_id = "default"
        
        channel = self.get_transmission_channel(channel_id)
        
        # Enhance vote data with metadata
        enhanced_vote = {
            **vote_data,
            'transmitted_at': datetime.utcnow().isoformat()
        }
        
        # Create encrypted envelope
        encrypted = VoteEncryption.encrypt_vote(enhanced_vote, self.master_key)
        envelope_hash = VoteEncryption.compute_envelope_hash(encrypted)
        transmission_id = secrets.token_hex(16)
        
        transmission_envelope = {
            'transmission_id': transmission_id,
            'channel_id': channel_id,
            'encrypted_vote': encrypted,
            'envelope_hash': envelope_hash,
            'prepared_at': datetime.utcnow().isoformat()
        }
        
        add_log(f"Vote prepared for transmission: {transmission_id}", "info")
        return transmission_envelope
    
    def receive_encrypted_vote(self, transmission_envelope: dict) -> bool:
        """
        Receive and store an encrypted vote transmission.
        
        Args:
            transmission_envelope: The received transmission envelope
            
        Returns:
            bool: True if successfully received and stored
            
        Raises:
            ValueError: If envelope is malformed or invalid
        """
        try:
            # Validate envelope structure
            required_fields = ['transmission_id', 'encrypted_vote', 'envelope_hash']
            if not all(field in transmission_envelope for field in required_fields):
                raise ValueError(f"Invalid transmission envelope - missing required fields")
            
            transmission_id = transmission_envelope['transmission_id']
            encrypted = transmission_envelope['encrypted_vote']
            claimed_hash = transmission_envelope['envelope_hash']
            
            # Verify envelope integrity
            computed_hash = VoteEncryption.compute_envelope_hash(encrypted)
            if computed_hash != claimed_hash:
                raise ValueError(
                    f"Envelope integrity check failed: "
                    f"claimed={claimed_hash[:16]}..., computed={computed_hash[:16]}..."
                )
            
            # Extract components
            nonce = encrypted['nonce']
            ciphertext = encrypted['ciphertext']
            tag = encrypted['tag']
            
            # Store encrypted ballot
            self.ballot_repo.add_encrypted_ballot(
                transmission_id, nonce, ciphertext, tag, claimed_hash
            )
            
            add_log(f"Encrypted vote received and stored: {transmission_id}", "info")
            return True
            
        except Exception as e:
            add_log(f"Error receiving encrypted vote: {str(e)}", "error")
            raise
    
    def decrypt_and_process_vote(self, transmission_id: str) -> dict:
        """
        Decrypt a received encrypted vote for processing.
        
        Args:
            transmission_id: The transmission ID of the vote to decrypt
            
        Returns:
            dict: Decrypted vote data
                 {
                     'voter_id': str,
                     'candidate': str,
                     'token_hash': str,
                     'timestamp': str,
                     'transmitted_at': str
                 }
                 
        Raises:
            ValueError: If decryption fails or transmission not found
        """
        if self.master_key is None:
            raise ValueError("Master encryption key not set for decryption.")
        
        # Retrieve encrypted ballot
        encrypted_ballot = self.ballot_repo.get_encrypted_ballot(transmission_id)
        if not encrypted_ballot:
            raise ValueError(f"Encrypted transmission not found: {transmission_id}")
        
        # Reconstruct encrypted envelope
        encrypted_envelope = {
            'nonce': encrypted_ballot['nonce'],
            'ciphertext': encrypted_ballot['ciphertext'],
            'tag': encrypted_ballot['tag']
        }
        
        # Verify integrity before decryption
        computed_hash = VoteEncryption.compute_envelope_hash(encrypted_envelope)
        if computed_hash != encrypted_ballot['envelope_hash']:
            raise ValueError(
                f"Envelope integrity check failed during decryption: {transmission_id}"
            )
        
        # Decrypt
        try:
            vote_data = VoteEncryption.decrypt_vote(encrypted_envelope, self.master_key)
            add_log(f"Vote decrypted successfully: {transmission_id}", "info")
            return vote_data
            
        except Exception as e:
            add_log(f"Vote decryption failed: {str(e)}", "error")
            raise
    
    def get_transmission_statistics(self) -> dict:
        """
        Get statistics about vote transmissions.
        
        Returns:
            dict: Statistics including total received, pending, etc.
        """
        total_encrypted = self.ballot_repo.get_encrypted_ballots_count()
        
        return {
            'total_encrypted_ballots': total_encrypted,
            'active_channels': len(self.channels),
            'algorithm': 'AES-256-GCM',
            'key_size_bits': VoteEncryption.KEY_SIZE * 8,
            'nonce_size_bits': VoteEncryption.NONCE_SIZE * 8,
            'tag_size_bits': VoteEncryption.TAG_SIZE * 8
        }
