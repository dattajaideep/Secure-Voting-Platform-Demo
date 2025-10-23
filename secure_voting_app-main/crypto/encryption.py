# crypto/encryption.py
"""
End-to-End Encryption Module for Vote Transmission

Implements AES-256-GCM authenticated encryption for securing votes
during transmission from voter to voting authority.

Features:
- AES-256 in GCM mode for authenticated encryption
- HMAC for additional authentication
- Secure key derivation using PBKDF2
- Nonce generation and management
- Support for encrypted vote envelopes
"""

import os
import secrets
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import json


class VoteEncryption:
    """
    Handles end-to-end encryption of votes during transmission.
    
    Uses AES-256-GCM for authenticated encryption with:
    - 256-bit keys (32 bytes)
    - 96-bit nonces (12 bytes) for GCM
    - 128-bit authentication tags (16 bytes)
    """
    
    # Encryption constants
    KEY_SIZE = 32  # 256-bit key
    NONCE_SIZE = 12  # 96-bit nonce (recommended for GCM)
    TAG_SIZE = 16  # 128-bit authentication tag
    SALT_SIZE = 16  # 128-bit salt for key derivation
    PBKDF2_ITERATIONS = 480000  # OWASP recommendation as of 2023
    
    def __init__(self):
        """Initialize the encryption handler."""
        self.backend = default_backend()
    
    @staticmethod
    def generate_key() -> bytes:
        """
        Generate a cryptographically secure random key for AES-256.
        
        Returns:
            bytes: 256-bit random key
        """
        return secrets.token_bytes(VoteEncryption.KEY_SIZE)
    
    @staticmethod
    def generate_nonce() -> bytes:
        """
        Generate a cryptographically secure random nonce for GCM.
        
        Returns:
            bytes: 96-bit random nonce (recommended for GCM)
        """
        return secrets.token_bytes(VoteEncryption.NONCE_SIZE)
    
    @staticmethod
    def derive_key_from_password(password: str, salt: bytes = None) -> tuple:
        """
        Derive an encryption key from a password using PBKDF2.
        
        Args:
            password: The password to derive from
            salt: Optional salt (generated if not provided)
            
        Returns:
            tuple: (derived_key, salt) - both as bytes
        """
        if salt is None:
            salt = secrets.token_bytes(VoteEncryption.SALT_SIZE)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=VoteEncryption.KEY_SIZE,
            salt=salt,
            iterations=VoteEncryption.PBKDF2_ITERATIONS,
            backend=default_backend()
        )
        key = kdf.derive(password.encode())
        return key, salt
    
    @staticmethod
    def encrypt_vote(vote_data: dict, encryption_key: bytes) -> dict:
        """
        Encrypt a vote using AES-256-GCM.
        
        Args:
            vote_data: Dictionary containing vote information
                      {
                          'voter_id': str,
                          'candidate': str,
                          'token_hash': str,
                          'timestamp': str
                      }
            encryption_key: 256-bit encryption key (32 bytes)
            
        Returns:
            dict: Encrypted vote envelope containing:
                {
                    'nonce': str (hex-encoded),
                    'ciphertext': str (hex-encoded),
                    'tag': str (hex-encoded),
                    'encrypted_at': str (ISO timestamp)
                }
                
        Raises:
            ValueError: If encryption key size is invalid
        """
        if len(encryption_key) != VoteEncryption.KEY_SIZE:
            raise ValueError(f"Key must be {VoteEncryption.KEY_SIZE} bytes, got {len(encryption_key)}")
        
        # Generate nonce
        nonce = VoteEncryption.generate_nonce()
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(encryption_key),
            modes.GCM(nonce),
            backend=default_backend()
        )
        
        encryptor = cipher.encryptor()
        
        # Serialize vote data
        plaintext = json.dumps(vote_data).encode('utf-8')
        
        # Encrypt
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        
        # Get authentication tag
        tag = encryptor.tag
        
        # Return encrypted envelope
        return {
            'nonce': nonce.hex(),
            'ciphertext': ciphertext.hex(),
            'tag': tag.hex(),
            'algorithm': 'AES-256-GCM'
        }
    
    @staticmethod
    def decrypt_vote(encrypted_envelope: dict, encryption_key: bytes) -> dict:
        """
        Decrypt a vote using AES-256-GCM.
        
        Args:
            encrypted_envelope: Dictionary with encrypted data
                               {
                                   'nonce': str (hex-encoded),
                                   'ciphertext': str (hex-encoded),
                                   'tag': str (hex-encoded)
                               }
            encryption_key: 256-bit encryption key (32 bytes)
            
        Returns:
            dict: Decrypted vote data
                 {
                     'voter_id': str,
                     'candidate': str,
                     'token_hash': str,
                     'timestamp': str
                 }
                 
        Raises:
            ValueError: If key size is invalid or decryption fails
            cryptography.hazmat.primitives.ciphers.InvalidTag: If authentication fails
        """
        if len(encryption_key) != VoteEncryption.KEY_SIZE:
            raise ValueError(f"Key must be {VoteEncryption.KEY_SIZE} bytes, got {len(encryption_key)}")
        
        # Extract components
        nonce = bytes.fromhex(encrypted_envelope['nonce'])
        ciphertext = bytes.fromhex(encrypted_envelope['ciphertext'])
        tag = bytes.fromhex(encrypted_envelope['tag'])
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(encryption_key),
            modes.GCM(nonce, tag),
            backend=default_backend()
        )
        
        decryptor = cipher.decryptor()
        
        try:
            # Decrypt and verify
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Deserialize
            vote_data = json.loads(plaintext.decode('utf-8'))
            return vote_data
            
        except Exception as e:
            raise ValueError(f"Vote decryption failed - authentication error: {str(e)}")
    
    @staticmethod
    def compute_envelope_hash(encrypted_envelope: dict) -> str:
        """
        Compute a hash of the encrypted envelope for integrity verification.
        
        Only hashes the cryptographic components (nonce, ciphertext, tag),
        not metadata like algorithm or timestamps.
        
        Args:
            encrypted_envelope: The encrypted vote envelope
            
        Returns:
            str: SHA-256 hash in hex format
        """
        # Only include cryptographic components for hash consistency
        crypto_components = {
            'nonce': encrypted_envelope.get('nonce'),
            'ciphertext': encrypted_envelope.get('ciphertext'),
            'tag': encrypted_envelope.get('tag')
        }
        # Create deterministic representation
        envelope_str = json.dumps(crypto_components, sort_keys=True)
        return hashlib.sha256(envelope_str.encode()).hexdigest()


class TransmissionChannel:
    """
    Represents a secure transmission channel for encrypted votes.
    
    Handles:
    - Shared key establishment
    - Vote envelope creation
    - Transmission receipt tracking
    """
    
    def __init__(self, channel_id: str):
        """
        Initialize a transmission channel.
        
        Args:
            channel_id: Unique identifier for this channel
        """
        self.channel_id = channel_id
        self.shared_key = VoteEncryption.generate_key()
        self.transmissions = {}  # Track sent/received votes
    
    def get_channel_key(self) -> bytes:
        """Get the shared encryption key for this channel."""
        return self.shared_key
    
    def create_encrypted_vote_envelope(self, vote_data: dict) -> dict:
        """
        Create an encrypted vote envelope for transmission.
        
        Args:
            vote_data: Vote information to encrypt
            
        Returns:
            dict: Complete transmission envelope with metadata
        """
        encrypted = VoteEncryption.encrypt_vote(vote_data, self.shared_key)
        envelope_hash = VoteEncryption.compute_envelope_hash(encrypted)
        
        return {
            'channel_id': self.channel_id,
            'encrypted_vote': encrypted,
            'envelope_hash': envelope_hash,
            'transmission_id': secrets.token_hex(16)
        }
    
    def verify_envelope_integrity(self, envelope: dict) -> bool:
        """
        Verify the integrity of a received envelope.
        
        Args:
            envelope: The transmission envelope
            
        Returns:
            bool: True if envelope hash matches, False otherwise
        """
        claimed_hash = envelope.get('envelope_hash')
        computed_hash = VoteEncryption.compute_envelope_hash(envelope['encrypted_vote'])
        return claimed_hash == computed_hash
