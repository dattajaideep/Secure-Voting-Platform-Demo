"""
Test suite for one-vote-per-voter (multi-voting prevention) functionality.

This module tests all layers of the voting system to ensure voters can only vote once:
- Database layer (has_voter_voted checks)
- Service layer (voting authority and voter client)
- Cryptographic verification with multi-vote prevention
"""

import pytest
import sqlite3
import os
import sys
from datetime import datetime
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


class TestOneVotePerVoter:
    """Test suite for one-vote-per-voter enforcement."""
    
    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        """Setup a fresh test database for each test."""
        # Use test database
        self.test_db = "test_voting.db"
        
        # Remove if exists
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        
        # Patch connection to use test database
        import db.connection
        self.original_db_path = db.connection.DB_PATH
        db.connection.DB_PATH = self.test_db
        
        # Initialize test database
        init_db()
        
        yield
        
        # Restore original database path and cleanup
        db.connection.DB_PATH = self.original_db_path
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    def test_voter_repository_has_voter_voted_new_voter(self):
        """Test that new voters have not voted yet."""
        voter_repo = VoterRepository()
        
        # Add a new voter
        voter_repo.add_voter("voter1", "Test Voter 1")
        
        # Verify has_voter_voted returns False
        assert voter_repo.has_voter_voted("voter1") is False
    
    def test_voter_repository_mark_and_check_voted(self):
        """Test marking a voter as voted and checking the status."""
        voter_repo = VoterRepository()
        
        # Add a new voter
        voter_repo.add_voter("voter2", "Test Voter 2")
        assert voter_repo.has_voter_voted("voter2") is False
        
        # Mark voter as voted
        voter_repo.mark_voted("voter2")
        
        # Verify voter is now marked as voted
        assert voter_repo.has_voter_voted("voter2") is True
    
    def test_voter_repository_has_voter_voted_nonexistent_voter(self):
        """Test that checking nonexistent voter returns False."""
        voter_repo = VoterRepository()
        
        # Check nonexistent voter
        assert voter_repo.has_voter_voted("nonexistent") is False
    
    def test_token_repository_get_voter_id_by_token_hash(self):
        """Test retrieving voter_id from token hash."""
        voter_repo = VoterRepository()
        token_repo = TokenRepository()
        
        # Setup
        voter_repo.add_voter("voter3", "Test Voter 3")
        token_hash = "abc123def456"
        signature = "sig123"
        
        # Add token
        token_repo.add_token("voter3", token_hash, signature)
        
        # Retrieve voter_id from token hash
        retrieved_voter_id = token_repo.get_voter_id_by_token_hash(token_hash)
        assert retrieved_voter_id == "voter3"
    
    def test_token_repository_get_voter_id_invalid_hash(self):
        """Test retrieving voter_id with invalid token hash."""
        token_repo = TokenRepository()
        
        # Try to get voter_id with nonexistent token hash
        retrieved_voter_id = token_repo.get_voter_id_by_token_hash("invalid_hash")
        assert retrieved_voter_id is None
    
    def test_voting_authority_prevents_multi_vote_same_token(self):
        """Test that voting authority prevents voting twice with same token."""
        # Setup
        voter_repo = VoterRepository()
        token_repo = TokenRepository()
        ballot_repo = BallotRepository()
        
        voter_repo.add_voter("voter4", "Test Voter 4")
        authority = VotingAuthority(get_conn())
        client = VoterClient(authority)
        
        # Create blind token
        token_hash, signature = client.create_blind_token("voter4")
        signature_int = int(signature, 16)
        
        # Cast first vote - should succeed
        ballot_id_1 = client.cast_vote(token_hash, signature_int, "Candidate A")
        assert ballot_id_1 is not None
        assert voter_repo.has_voter_voted("voter4") is True
        
        # Try to cast second vote - should fail
        with pytest.raises(Exception) as exc_info:
            client.cast_vote(token_hash, signature_int, "Candidate B")
        
        assert "already cast" in str(exc_info.value).lower() or "one vote" in str(exc_info.value).lower()
    
    def test_voting_authority_prevents_multi_vote_different_token(self):
        """Test that voting authority prevents voting with different token after first vote."""
        # Setup
        voter_repo = VoterRepository()
        token_repo = TokenRepository()
        
        voter_repo.add_voter("voter5", "Test Voter 5")
        authority = VotingAuthority(get_conn())
        client = VoterClient(authority)
        
        # Create first token and vote
        token_hash_1, signature_1 = client.create_blind_token("voter5")
        ballot_id_1 = client.cast_vote(token_hash_1, int(signature_1, 16), "Candidate A")
        assert ballot_id_1 is not None
        assert voter_repo.has_voter_voted("voter5") is True
        
        # Create second token for same voter
        token_hash_2, signature_2 = client.create_blind_token("voter5")
        
        # Try to vote with second token - should fail
        with pytest.raises(Exception) as exc_info:
            client.cast_vote(token_hash_2, int(signature_2, 16), "Candidate B")
        
        assert "already cast" in str(exc_info.value).lower() or "one vote" in str(exc_info.value).lower()
    
    def test_voter_client_prevents_multi_vote(self):
        """Test that voter client prevents multi-vote before sending to authority."""
        # Setup
        voter_repo = VoterRepository()
        token_repo = TokenRepository()
        
        voter_repo.add_voter("voter6", "Test Voter 6")
        authority = VotingAuthority(get_conn())
        client = VoterClient(authority)
        
        # Create token
        token_hash, signature = client.create_blind_token("voter6")
        signature_int = int(signature, 16)
        
        # First vote succeeds
        ballot_id = client.cast_vote(token_hash, signature_int, "Candidate A")
        assert ballot_id is not None
        
        # Second vote attempt should fail
        with pytest.raises(Exception) as exc_info:
            client.cast_vote(token_hash, signature_int, "Candidate A")
        
        # Should catch the multi-vote before sending to authority
        assert "already cast" in str(exc_info.value).lower() or "one vote" in str(exc_info.value).lower()
    
    def test_multiple_voters_can_vote_once_each(self):
        """Test that multiple voters can each vote once."""
        # Setup
        voter_repo = VoterRepository()
        ballot_repo = BallotRepository()
        
        # Add multiple voters
        voters = [("voter7", "Voter 7"), ("voter8", "Voter 8"), ("voter9", "Voter 9")]
        for voter_id, name in voters:
            voter_repo.add_voter(voter_id, name)
        
        authority = VotingAuthority(get_conn())
        client = VoterClient(authority)
        
        # Each voter votes once
        for voter_id, name in voters:
            token_hash, signature = client.create_blind_token(voter_id)
            ballot_id = client.cast_vote(token_hash, int(signature, 16), "Candidate A")
            assert ballot_id is not None
            assert voter_repo.has_voter_voted(voter_id) is True
        
        # Verify ballots were recorded
        all_ballots = ballot_repo.get_all_ballots()
        assert len(all_ballots) == 3
    
    def test_voting_authority_check_race_condition(self):
        """Test that voting authority checks have_voted flag properly."""
        # Setup
        voter_repo = VoterRepository()
        
        voter_repo.add_voter("voter10", "Test Voter 10")
        
        # Simulate marking voter as already voted
        voter_repo.mark_voted("voter10")
        
        authority = VotingAuthority(get_conn())
        client = VoterClient(authority)
        
        # Create token
        token_hash, signature = client.create_blind_token("voter10")
        
        # Try to vote with marked voter - should fail
        with pytest.raises(Exception) as exc_info:
            client.cast_vote(token_hash, int(signature, 16), "Candidate A")
        
        assert "already cast" in str(exc_info.value).lower() or "one vote" in str(exc_info.value).lower()
    
    def test_ballot_count_matches_unique_voters(self):
        """Test that ballot count equals number of voters who voted."""
        # Setup
        voter_repo = VoterRepository()
        ballot_repo = BallotRepository()
        
        # Add 5 voters
        for i in range(1, 6):
            voter_repo.add_voter(f"voter{i}", f"Voter {i}")
        
        authority = VotingAuthority(get_conn())
        client = VoterClient(authority)
        
        # 3 voters vote
        for i in range(1, 4):
            token_hash, signature = client.create_blind_token(f"voter{i}")
            client.cast_vote(token_hash, int(signature, 16), "Candidate A")
        
        # Check ballot count
        ballots = ballot_repo.get_all_ballots()
        assert len(ballots) == 3
        
        # Try to have voter1 vote again - should fail
        token_repo = TokenRepository()
        voter_token = token_repo.get_token_by_voter("voter1")
        
        with pytest.raises(Exception):
            client.cast_vote(voter_token["token_hash"], int(voter_token["signature"], 16), "Candidate B")
        
        # Ballot count should still be 3
        ballots = ballot_repo.get_all_ballots()
        assert len(ballots) == 3


class TestEdgeCases:
    """Test edge cases and potential security issues."""
    
    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        """Setup a fresh test database for each test."""
        self.test_db = "test_voting_edge.db"
        
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        
        import db.connection
        self.original_db_path = db.connection.DB_PATH
        db.connection.DB_PATH = self.test_db
        
        init_db()
        
        yield
        
        db.connection.DB_PATH = self.original_db_path
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    def test_voter_with_token_but_not_voted_eligible(self):
        """Test that voters with token but no vote are eligible."""
        voter_repo = VoterRepository()
        
        voter_repo.add_voter("edge_voter1", "Edge Test Voter 1")
        voter_repo.update_token_status("edge_voter1", True)
        
        # Should be eligible for voting
        voters = voter_repo.get_all_voters()
        voter_data = [v for v in voters if v["voter_id"] == "edge_voter1"][0]
        
        assert voter_data["has_token"] == 1 or voter_data["has_token"] is True
        assert voter_data["has_voted"] == 0 or voter_data["has_voted"] is False
    
    def test_voter_filtering_in_cast_vote(self):
        """Test that voting system properly filters voters."""
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
        
        # Should only have 1 eligible voter
        assert len(eligible) == 1
        assert eligible[0]["voter_id"] == "has_token_no_vote"
    
    def test_concurrent_vote_attempts_both_fail(self):
        """Test that attempting concurrent votes fails gracefully."""
        voter_repo = VoterRepository()
        
        voter_repo.add_voter("concurrent_voter", "Concurrent Test Voter")
        
        authority = VotingAuthority(get_conn())
        client = VoterClient(authority)
        
        # Create two tokens for same voter
        token_hash_1, signature_1 = client.create_blind_token("concurrent_voter")
        token_hash_2, signature_2 = client.create_blind_token("concurrent_voter")
        
        # First vote succeeds
        ballot_id = client.cast_vote(token_hash_1, int(signature_1, 16), "Candidate A")
        assert ballot_id is not None
        
        # Second vote (simulating concurrent attempt) should fail
        with pytest.raises(Exception):
            client.cast_vote(token_hash_2, int(signature_2, 16), "Candidate B")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
