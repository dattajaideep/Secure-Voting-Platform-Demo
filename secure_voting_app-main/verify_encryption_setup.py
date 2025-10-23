#!/usr/bin/env python3
# verify_encryption_setup.py
"""
Verification script for end-to-end encryption setup.

Validates that the encryption system is properly configured and functioning.
"""

import sys
import os

def verify_imports():
    """Verify that all required libraries are installed."""
    print("=" * 70)
    print("VERIFYING IMPORTS")
    print("=" * 70)
    
    imports = [
        ('cryptography', 'Cryptography library'),
        ('crypto.encryption', 'Vote encryption module'),
        ('services.vote_transmission', 'Vote transmission service'),
        ('db.repositories.encrypted_ballot_repository', 'Encrypted ballot repository'),
    ]
    
    for import_name, description in imports:
        try:
            __import__(import_name)
            print(f"✓ {description:50} OK")
        except ImportError as e:
            print(f"✗ {description:50} FAILED")
            print(f"  Error: {str(e)}")
            return False
    
    return True


def verify_encryption_functions():
    """Verify encryption functions work correctly."""
    print("\n" + "=" * 70)
    print("VERIFYING ENCRYPTION FUNCTIONS")
    print("=" * 70)
    
    try:
        from crypto.encryption import VoteEncryption
        from datetime import datetime
        
        # Test 1: Key generation
        print("\n1. Testing key generation...")
        key = VoteEncryption.generate_key()
        assert len(key) == 32, f"Key size mismatch: {len(key)} != 32"
        print(f"   ✓ Generated {len(key)}-byte key")
        
        # Test 2: Nonce generation
        print("2. Testing nonce generation...")
        nonce = VoteEncryption.generate_nonce()
        assert len(nonce) == 12, f"Nonce size mismatch: {len(nonce)} != 12"
        print(f"   ✓ Generated {len(nonce)}-byte nonce")
        
        # Test 3: Vote encryption/decryption
        print("3. Testing vote encryption and decryption...")
        vote_data = {
            'voter_id': 'test_voter',
            'candidate': 'Test Candidate',
            'token_hash': 'test_hash_123',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        encrypted = VoteEncryption.encrypt_vote(vote_data, key)
        print(f"   ✓ Encrypted vote: {len(encrypted['ciphertext'])//2} bytes")
        
        decrypted = VoteEncryption.decrypt_vote(encrypted, key)
        assert decrypted['voter_id'] == vote_data['voter_id'], "Voter ID mismatch"
        assert decrypted['candidate'] == vote_data['candidate'], "Candidate mismatch"
        print(f"   ✓ Decrypted vote matches original")
        
        # Test 4: Authentication failure
        print("4. Testing authentication failure detection...")
        wrong_key = VoteEncryption.generate_key()
        try:
            VoteEncryption.decrypt_vote(encrypted, wrong_key)
            print("   ✗ Authentication check FAILED - wrong key accepted!")
            return False
        except ValueError as e:
            if "authentication error" in str(e):
                print(f"   ✓ Authentication failure detected correctly")
            else:
                print(f"   ✗ Wrong error type: {str(e)}")
                return False
        
        # Test 5: Envelope hash
        print("5. Testing envelope hash...")
        hash1 = VoteEncryption.compute_envelope_hash(encrypted)
        hash2 = VoteEncryption.compute_envelope_hash(encrypted)
        assert hash1 == hash2, "Hash computation not deterministic"
        assert len(hash1) == 64, f"Hash length mismatch: {len(hash1)} != 64"
        print(f"   ✓ Envelope hash: {hash1[:16]}... (SHA-256)")
        
        print("\n✓ All encryption function tests PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Encryption test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def verify_database_schema():
    """Verify database schema includes encrypted ballots table."""
    print("\n" + "=" * 70)
    print("VERIFYING DATABASE SCHEMA")
    print("=" * 70)
    
    try:
        from db.connection import get_conn
        from db.init_db import init_db
        
        print("\n1. Initializing database...")
        init_db()
        print("   ✓ Database initialized")
        
        print("2. Checking encrypted_ballots table...")
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(encrypted_ballots)")
        columns = cursor.fetchall()
        
        required_columns = [
            'id', 'transmission_id', 'nonce', 'ciphertext', 
            'tag', 'envelope_hash', 'received_at'
        ]
        
        found_columns = [col[1] for col in columns]
        
        for col in required_columns:
            if col in found_columns:
                print(f"   ✓ Column '{col}' exists")
            else:
                print(f"   ✗ Column '{col}' MISSING")
                return False
        
        print("\n✓ Database schema verification PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Database verification FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def verify_transmission_service():
    """Verify vote transmission service."""
    print("\n" + "=" * 70)
    print("VERIFYING TRANSMISSION SERVICE")
    print("=" * 70)
    
    try:
        from services.vote_transmission import VoteTransmissionService
        from crypto.encryption import VoteEncryption
        from datetime import datetime
        
        print("\n1. Initializing transmission service...")
        service = VoteTransmissionService()
        print("   ✓ Service initialized")
        
        print("2. Setting master encryption key...")
        key = VoteEncryption.generate_key()
        service.set_master_encryption_key(key)
        print("   ✓ Master key set")
        
        print("3. Creating transmission channel...")
        channel_id = service.create_transmission_channel()
        print(f"   ✓ Channel created: {channel_id}")
        
        print("4. Preparing vote for transmission...")
        vote_data = {
            'voter_id': 'test_voter_ts',
            'candidate': 'Test Candidate',
            'token_hash': 'test_hash_ts',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        envelope = service.prepare_vote_for_transmission(vote_data)
        assert 'transmission_id' in envelope
        assert 'encrypted_vote' in envelope
        assert 'envelope_hash' in envelope
        print(f"   ✓ Vote prepared: {envelope['transmission_id'][:16]}...")
        
        print("5. Getting transmission statistics...")
        stats = service.get_transmission_statistics()
        print(f"   ✓ Algorithm: {stats['algorithm']}")
        print(f"   ✓ Key size: {stats['key_size_bits']} bits")
        print(f"   ✓ Nonce size: {stats['nonce_size_bits']} bits")
        print(f"   ✓ Tag size: {stats['tag_size_bits']} bits")
        
        print("\n✓ Transmission service verification PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Transmission service verification FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def verify_voting_authority():
    """Verify voting authority encryption support."""
    print("\n" + "=" * 70)
    print("VERIFYING VOTING AUTHORITY")
    print("=" * 70)
    
    try:
        from services.voting_authority import VotingAuthority
        from db.connection import get_conn
        
        print("\n1. Initializing voting authority...")
        db = get_conn()
        authority = VotingAuthority(db)
        print("   ✓ Authority initialized")
        
        print("2. Checking encryption key...")
        key = authority.get_encryption_key()
        assert key is not None, "Encryption key is None"
        assert len(key) == 32, f"Key size mismatch: {len(key)} != 32"
        print(f"   ✓ Encryption key available: {len(key)} bytes")
        
        print("3. Checking public key...")
        pub_key = authority.get_public_key()
        assert 'n' in pub_key and 'e' in pub_key, "Invalid public key"
        print(f"   ✓ Public key available: n={len(str(pub_key['n']))} digits")
        
        print("\n✓ Voting authority verification PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Voting authority verification FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "ENCRYPTION SETUP VERIFICATION" + " " * 24 + "║")
    print("╚" + "=" * 68 + "╝")
    
    results = []
    
    # Run all verifications
    results.append(("Imports", verify_imports()))
    results.append(("Encryption Functions", verify_encryption_functions()))
    results.append(("Database Schema", verify_database_schema()))
    results.append(("Transmission Service", verify_transmission_service()))
    results.append(("Voting Authority", verify_voting_authority()))
    
    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name:40} {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL VERIFICATIONS PASSED - ENCRYPTION SETUP IS VALID")
        print("=" * 70)
        return 0
    else:
        print("✗ SOME VERIFICATIONS FAILED - PLEASE CHECK ERRORS ABOVE")
        print("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
