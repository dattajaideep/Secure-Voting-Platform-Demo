# db/repositories/voter_repository.py
from db.connection import get_conn
from utils.logger import add_log
from utils.password_utils import hash_password, verify_password, encode_hash_salt, decode_hash_salt

class VoterRepository:
    def add_voter(self, voter_id: str, name: str):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR IGNORE INTO voters (voter_id, name, has_token, has_voted)
            VALUES (?, ?, 0, 0)
        """, (voter_id, name))
        conn.commit()
        conn.close()
        add_log(f"Added voter {name} ({voter_id})", "info")

    def get_all_voters(self):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM voters ORDER BY voter_id")
        result = cur.fetchall()
        conn.close()
        return [dict(r) for r in result]

    def update_token_status(self, voter_id: str, has_token: bool):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE voters SET has_token = ? WHERE voter_id = ?", (has_token, voter_id))
        conn.commit()
        conn.close()
        add_log(f"Updated token status for {voter_id} → {has_token}", "info")

    def mark_voted(self, voter_id: str):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE voters SET has_voted = 1 WHERE voter_id = ?", (voter_id,))
        conn.commit()
        conn.close()
        add_log(f"Voter {voter_id} marked as voted", "info")

    def get_voter_by_email(self, email: str):
        """
        Get voter information by email (voter_id).
        
        Args:
            email: The voter's email address (used as voter_id)
            
        Returns:
            Dictionary with voter information or None if not found
        """
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM voters WHERE voter_id = ?", (email,))
        result = cur.fetchone()
        conn.close()
        
        if result is None:
            return None
        
        return dict(result)

    def update_vote_status(self, email: str, voted: bool):
        """
        Update voter's voted status.
        
        Args:
            email: The voter's email address (used as voter_id)
            voted: Boolean indicating if voter has voted
        """
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE voters SET has_voted = ? WHERE voter_id = ?", (voted, email))
        conn.commit()
        conn.close()
        add_log(f"Updated vote status for {email} → {voted}", "info")

    def has_voter_voted(self, voter_id: str) -> bool:
        """
        Check if a voter has already cast their vote.
        
        Args:
            voter_id: The voter's unique identifier
            
        Returns:
            True if voter has already voted, False otherwise
        """
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT has_voted FROM voters WHERE voter_id = ?", (voter_id,))
        result = cur.fetchone()
        conn.close()
        
        if result is None:
            return False
        
        return bool(result['has_voted'])
