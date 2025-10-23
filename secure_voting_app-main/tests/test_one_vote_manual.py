"""
Test suite for one-vote-per-voter functionality.
Can be run as pytest tests or as standalone script.
"""

import sqlite3
import os
import sys
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.init_db import init_db
from db.connection import get_conn
from db.repositories.voter_repository import VoterRepository
from db.repositories.token_repository import TokenRepository
from db.repositories.ballot_repository import BallotRepository
from services.voter_client import VoterClient
from services.voting_authority import VotingAuthority


def setup_test_db():
    """Setup a fresh test database."""
    test_db = "test_voting_manual.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    import db.connection
    db.connection.DB_PATH = test_db
    init_db()
    return test_db


def cleanup_test_db(test_db):
    """Cleanup test database."""
    if os.path.exists(test_db):
        os.remove(test_db)


def test_voter_has_voted_check():
    """Test that has_voter_voted works correctly."""
    test_db = setup_test_db()
    try:
        voter_repo = VoterRepository()
        
        # Test 1: New voter should not have voted
        voter_repo.add_voter("voter1", "Test Voter 1")
        assert voter_repo.has_voter_voted("voter1") is False, "New voter should not have voted"
        
        # Test 2: Marked voter should have voted
        voter_repo.mark_voted("voter1")
        assert voter_repo.has_voter_voted("voter1") is True, "Marked voter should have voted"
        
        # Test 3: Nonexistent voter should return False
        assert voter_repo.has_voter_voted("nonexistent") is False, "Nonexistent voter should return False"
        
        print("✅ test_voter_has_voted_check PASSED")
    except Exception as e:
        print(f"❌ test_voter_has_voted_check FAILED: {e}")
        raise
    finally:
        cleanup_test_db(test_db)


def test_token_voter_id_lookup():
    """Test token to voter_id lookup."""
    test_db = setup_test_db()
    try:
        voter_repo = VoterRepository()
        token_repo = TokenRepository()
        
        voter_repo.add_voter("voter2", "Test Voter 2")
        token_hash = "abc123def456"
        signature = "sig123"
        
        token_repo.add_token("voter2", token_hash, signature)
        retrieved_voter_id = token_repo.get_voter_id_by_token_hash(token_hash)
        
        assert retrieved_voter_id == "voter2", f"Expected voter2, got {retrieved_voter_id}"
        
        # Test invalid hash
        assert token_repo.get_voter_id_by_token_hash("invalid") is None, "Invalid hash should return None"
        
        print("✅ test_token_voter_id_lookup PASSED")
    except Exception as e:
        print(f"❌ test_token_voter_id_lookup FAILED: {e}")
        raise
    finally:
        cleanup_test_db(test_db)


def test_single_vote_per_voter():
    """Test that voters can only vote once."""
    test_db = setup_test_db()
    try:
        voter_repo = VoterRepository()
        token_repo = TokenRepository()
        ballot_repo = BallotRepository()
        
        voter_repo.add_voter("voter3", "Test Voter 3")
        authority = VotingAuthority(get_conn())
        client = VoterClient(authority)
        
        # Create token
        token_hash, signature = client.create_blind_token("voter3")
        signature_int = int(signature, 16)
        
        # First vote should succeed
        ballot_id_1 = client.cast_vote(token_hash, signature_int, "Candidate A")
        assert ballot_id_1 is not None, "First vote should succeed"
        assert voter_repo.has_voter_voted("voter3"), "Voter should be marked as voted"
        
        # Second vote should fail
        try:
            ballot_id_2 = client.cast_vote(token_hash, signature_int, "Candidate B")
            raise AssertionError(f"Second vote should have failed but succeeded with ballot {ballot_id_2}")
        except Exception as e:
            if "already cast" in str(e).lower() or "one vote" in str(e).lower():
                print("✅ test_single_vote_per_voter PASSED")
            else:
                raise AssertionError(f"Wrong error message: {e}")
    except Exception as e:
        print(f"❌ test_single_vote_per_voter FAILED: {e}")
        raise
    finally:
        cleanup_test_db(test_db)


def test_multiple_voters():
    """Test that multiple voters can each vote once."""
    test_db = setup_test_db()
    try:
        voter_repo = VoterRepository()
        ballot_repo = BallotRepository()
        
        authority = VotingAuthority(get_conn())
        client = VoterClient(authority)
        
        # Add 3 voters and have each vote
        for i in range(1, 4):
            voter_id = f"voter{i}"
            voter_repo.add_voter(voter_id, f"Test Voter {i}")
            # Register voter with authority
            authority.register_voter(voter_id)
            token_hash, signature = client.create_blind_token(voter_id)
            ballot_id = client.cast_vote(token_hash, int(signature, 16), "Candidate A")
            assert ballot_id is not None, f"Vote for {voter_id} should succeed"
        
        # Check ballot count
        ballots = ballot_repo.get_all_ballots()
        assert len(ballots) == 3, f"Expected 3 ballots, got {len(ballots)}"
        
        print("✅ test_multiple_voters PASSED")
    except Exception as e:
        print(f"❌ test_multiple_voters FAILED: {e}")
        raise
    finally:
        cleanup_test_db(test_db)


def test_voter_filtering():
    """Test that voting system properly filters eligible voters."""
    test_db = setup_test_db()
    try:
        voter_repo = VoterRepository()
        
        # Add voters in different states
        voter_repo.add_voter("no_token", "No Token Voter")
        voter_repo.add_voter("has_token_no_vote", "Has Token Voter")
        voter_repo.add_voter("voted_already", "Already Voted")
        
        voter_repo.update_token_status("has_token_no_vote", True)
        voter_repo.update_token_status("voted_already", True)
        voter_repo.mark_voted("voted_already")
        
        # Get all voters
        all_voters = voter_repo.get_all_voters()
        
        # Filter eligible voters (has_token and not has_voted)
        eligible = [v for v in all_voters if v["has_token"] and not v["has_voted"]]
        
        assert len(eligible) == 1, f"Expected 1 eligible voter, got {len(eligible)}"
        assert eligible[0]["voter_id"] == "has_token_no_vote", "Wrong voter marked as eligible"
        
        print("✅ test_voter_filtering PASSED")
    except Exception as e:
        print(f"❌ test_voter_filtering FAILED: {e}")
        raise
    finally:
        cleanup_test_db(test_db)


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("ONE-VOTE-PER-VOTER TEST SUITE")
    print("="*70 + "\n")
    
    tests = [
        test_voter_has_voted_check,
        test_token_voter_id_lookup,
        test_single_vote_per_voter,
        test_multiple_voters,
        test_voter_filtering,
    ]
    
    results = []
    for test in tests:
        results.append(test())
        print()
    
    # Summary
    print("="*70)
    passed = sum(results)
    total = len(results)
    print(f"SUMMARY: {passed}/{total} tests passed")
    print("="*70 + "\n")
    
    return all(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
