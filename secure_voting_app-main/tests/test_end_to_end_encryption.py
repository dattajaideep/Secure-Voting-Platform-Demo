# tests/test_end_to_end_encryption.py
"""
Test Suite for End-to-End Encryption in Vote Transmission

Tests cover:
1. AES-256-GCM encryption/decryption
2. Vote envelope creation and integrity
3. Encrypted transmission workflow
4. Authority-side decryption and processing
5. Key derivation and management
"""

import pytest
import json
import secrets
from datetime import datetime
from crypto.encryption import VoteEncryption, TransmissionChannel
from services.vote_transmission import VoteTransmissionService
from services.voting_authority import VotingAuthority
from services.voter_client import VoterClient
from db.connection import get_conn
from db.init_db import init_db


class TestVoteEncryption:
    """Tests for the VoteEncryption class."""
    
    def test_generate_key(self):
        """Test that keys are generated with correct size."""
        key = VoteEncryption.generate_key()
        assert len(key) == VoteEncryption.KEY_SIZE
        assert isinstance(key, bytes)
    
    def test_generate_nonce(self):
        """Test that nonces are generated with correct size."""
        nonce = VoteEncryption.generate_nonce()
        assert len(nonce) == VoteEncryption.NONCE_SIZE
        assert isinstance(nonce, bytes)
    
    def test_generate_multiple_nonces_unique(self):
        """Test that each generated nonce is unique."""
        nonces = [VoteEncryption.generate_nonce() for _ in range(100)]
        assert len(set(nonces)) == 100  # All unique
    
    def test_derive_key_from_password(self):
        """Test password-based key derivation."""
        password = "secure_voting_password_123"
        key1, salt1 = VoteEncryption.derive_key_from_password(password)
        
        # Same password with same salt should produce same key
        key2, _ = VoteEncryption.derive_key_from_password(password, salt1)
        
        assert key1 == key2
        assert len(key1) == VoteEncryption.KEY_SIZE
        assert len(salt1) == VoteEncryption.SALT_SIZE
    
    def test_derive_key_different_passwords(self):
        """Test that different passwords produce different keys."""
        password1 = "password_one"
        password2 = "password_two"
        
        key1, salt = VoteEncryption.derive_key_from_password(password1)
        key2, _ = VoteEncryption.derive_key_from_password(password2, salt)
        
        assert key1 != key2
    
    def test_encrypt_decrypt_vote(self):
        """Test basic vote encryption and decryption."""
        vote_data = {
            'voter_id': 'voter_001',
            'candidate': 'Candidate A',
            'token_hash': 'abc123def456',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        key = VoteEncryption.generate_key()
        
        # Encrypt
        encrypted = VoteEncryption.encrypt_vote(vote_data, key)
        assert 'nonce' in encrypted
        assert 'ciphertext' in encrypted
        assert 'tag' in encrypted
        assert encrypted['algorithm'] == 'AES-256-GCM'
        
        # Decrypt
        decrypted = VoteEncryption.decrypt_vote(encrypted, key)
        
        assert decrypted['voter_id'] == vote_data['voter_id']
        assert decrypted['candidate'] == vote_data['candidate']
        assert decrypted['token_hash'] == vote_data['token_hash']
    
    def test_encrypt_decrypt_with_wrong_key_fails(self):
        """Test that decryption with wrong key fails."""
        vote_data = {
            'voter_id': 'voter_002',
            'candidate': 'Candidate B',
            'token_hash': 'xyz789',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        key1 = VoteEncryption.generate_key()
        key2 = VoteEncryption.generate_key()
        
        encrypted = VoteEncryption.encrypt_vote(vote_data, key1)
        
        # Should fail with wrong key
        with pytest.raises(ValueError, match="authentication error"):
            VoteEncryption.decrypt_vote(encrypted, key2)
    
    def test_encryption_deterministic_output_same_input(self):
        """Test that same data produces different ciphertexts (due to random nonce)."""
        vote_data = {
            'voter_id': 'voter_003',
            'candidate': 'Candidate C',
            'token_hash': 'test_hash',
            'timestamp': '2025-10-23T12:00:00'
        }
        
        key = VoteEncryption.generate_key()
        
        encrypted1 = VoteEncryption.encrypt_vote(vote_data, key)
        encrypted2 = VoteEncryption.encrypt_vote(vote_data, key)
        
        # Nonces should be different
        assert encrypted1['nonce'] != encrypted2['nonce']
        # Ciphertexts should be different
        assert encrypted1['ciphertext'] != encrypted2['ciphertext']
    
    def test_envelope_hash_computation(self):
        """Test that envelope hash is computed consistently."""
        envelope = {
            'nonce': 'abc123',
            'ciphertext': 'xyz789',
            'tag': 'tag123'
        }
        
        hash1 = VoteEncryption.compute_envelope_hash(envelope)
        hash2 = VoteEncryption.compute_envelope_hash(envelope)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex digest is 64 chars
    
    def test_envelope_hash_different_for_different_envelopes(self):
        """Test that different envelopes produce different hashes."""
        envelope1 = {'nonce': 'a', 'ciphertext': 'b', 'tag': 'c'}
        envelope2 = {'nonce': 'x', 'ciphertext': 'y', 'tag': 'z'}
        
        hash1 = VoteEncryption.compute_envelope_hash(envelope1)
        hash2 = VoteEncryption.compute_envelope_hash(envelope2)
        
        assert hash1 != hash2


class TestTransmissionChannel:
    """Tests for the TransmissionChannel class."""
    
    def test_channel_creation(self):
        """Test transmission channel creation."""
        channel = TransmissionChannel("test_channel_1")
        assert channel.channel_id == "test_channel_1"
        assert channel.get_channel_key() is not None
        assert len(channel.get_channel_key()) == VoteEncryption.KEY_SIZE
    
    def test_create_encrypted_vote_envelope(self):
        """Test encrypted vote envelope creation."""
        channel = TransmissionChannel("test_channel_2")
        vote_data = {
            'voter_id': 'voter_004',
            'candidate': 'Candidate A',
            'token_hash': 'test_hash_004',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        envelope = channel.create_encrypted_vote_envelope(vote_data)
        
        assert 'channel_id' in envelope
        assert 'encrypted_vote' in envelope
        assert 'envelope_hash' in envelope
        assert 'transmission_id' in envelope
        assert envelope['channel_id'] == 'test_channel_2'
    
    def test_verify_envelope_integrity(self):
        """Test envelope integrity verification."""
        channel = TransmissionChannel("test_channel_3")
        vote_data = {
            'voter_id': 'voter_005',
            'candidate': 'Candidate B',
            'token_hash': 'test_hash_005',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        envelope = channel.create_encrypted_vote_envelope(vote_data)
        
        # Should verify successfully
        assert channel.verify_envelope_integrity(envelope) is True
        
        # Modify envelope hash - should fail
        envelope['envelope_hash'] = 'tampered_hash'
        assert channel.verify_envelope_integrity(envelope) is False


class TestVoteTransmissionService:
    """Tests for the VoteTransmissionService class."""
    
    def setup_method(self):
        """Setup for each test."""
        self.service = VoteTransmissionService()
        self.key = VoteEncryption.generate_key()
        self.service.set_master_encryption_key(self.key)
    
    def test_set_master_encryption_key(self):
        """Test setting master encryption key."""
        key = VoteEncryption.generate_key()
        self.service.set_master_encryption_key(key)
        assert self.service.master_key == key
    
    def test_set_invalid_key_size(self):
        """Test that invalid key size raises error."""
        invalid_key = b"short_key"
        with pytest.raises(ValueError, match="Key must be"):
            self.service.set_master_encryption_key(invalid_key)
    
    def test_create_transmission_channel(self):
        """Test transmission channel creation."""
        channel_id = self.service.create_transmission_channel()
        assert channel_id in self.service.channels
        
        # With custom ID
        custom_id = "custom_channel"
        channel_id = self.service.create_transmission_channel(custom_id)
        assert channel_id == custom_id
        assert custom_id in self.service.channels
    
    def test_prepare_vote_for_transmission(self):
        """Test vote preparation for transmission."""
        vote_data = {
            'voter_id': 'voter_006',
            'candidate': 'Candidate C',
            'token_hash': 'test_hash_006',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        envelope = self.service.prepare_vote_for_transmission(vote_data)
        
        assert 'transmission_id' in envelope
        assert 'channel_id' in envelope
        assert 'encrypted_vote' in envelope
        assert 'envelope_hash' in envelope
        assert 'prepared_at' in envelope
    
    def test_prepare_vote_without_key_fails(self):
        """Test that preparing vote without key fails."""
        service = VoteTransmissionService()
        vote_data = {
            'voter_id': 'voter_007',
            'candidate': 'Candidate D',
            'token_hash': 'test_hash_007',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        with pytest.raises(ValueError, match="Master encryption key not set"):
            service.prepare_vote_for_transmission(vote_data)
    
    def test_transmission_statistics(self):
        """Test transmission statistics retrieval."""
        stats = self.service.get_transmission_statistics()
        
        assert 'total_encrypted_ballots' in stats
        assert 'active_channels' in stats
        assert 'algorithm' in stats
        assert stats['algorithm'] == 'AES-256-GCM'
        assert stats['key_size_bits'] == 256
        assert stats['nonce_size_bits'] == 96
        assert stats['tag_size_bits'] == 128


class TestEncryptedVoteWorkflow:
    """Integration tests for the complete encrypted voting workflow."""
    
    def setup_method(self):
        """Setup database and services for each test."""
        self.db = get_conn()
        init_db()
        
        # Create test voter
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO voters (voter_id, name, password_hash, password_salt)
            VALUES (?, ?, ?, ?)
        """, ('test_voter_001', 'Test Voter', 'hash', 'salt'))
        self.db.commit()
        
        self.authority = VotingAuthority(self.db)
        self.authority.register_voter('test_voter_001')
    
    def teardown_method(self):
        """Clean up after each test."""
        # Clear the ballots table to avoid vote conflicts
        cursor = self.db.cursor()
        cursor.execute("DELETE FROM ballots")
        cursor.execute("DELETE FROM voters")
        self.db.commit()
        self.db.close()
    
    def test_complete_encrypted_vote_workflow(self):
        """Test complete workflow from vote encryption to decryption."""
        # Create voter client
        transmission_service = VoteTransmissionService()
        transmission_service.set_master_encryption_key(self.authority.get_encryption_key())
        client = VoterClient(self.authority, transmission_service)
        
        # Create blind token
        token_hash, signature = client.create_blind_token('test_voter_001')
        
        # Cast encrypted vote
        result = client.cast_vote(token_hash, int(signature, 16), 'Candidate A')
        
        assert result['status'] == 'success'
        assert result['encrypted'] is True
        assert 'ballot_id' in result
        assert 'transmission_id' in result
    
    def test_encrypted_vote_integrity(self):
        """Test that encrypted votes maintain integrity through transmission."""
        # Use the same service and key as setup
        transmission_service = VoteTransmissionService()
        transmission_service.set_master_encryption_key(self.authority.get_encryption_key())
        
        vote_data = {
            'voter_id': 'voter_008',
            'candidate': 'Candidate E',
            'token_hash': 'test_hash_008',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Prepare transmission
        envelope = transmission_service.prepare_vote_for_transmission(vote_data)
        
        # Simulate receiving
        transmission_service.receive_encrypted_vote(envelope)
        
        # Decrypt and verify
        decrypted = transmission_service.decrypt_and_process_vote(envelope['transmission_id'])
        
        assert decrypted['voter_id'] == vote_data['voter_id']
        assert decrypted['candidate'] == vote_data['candidate']
        assert decrypted['token_hash'] == vote_data['token_hash']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
