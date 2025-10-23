# db/repositories/token_repository.py
from db.connection import get_conn


class TokenRepository:
    def add_token(self, voter_id, token_hash, signature):
        """Add a blind token for a voter"""
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO tokens (voter_id, token_hash, signature) VALUES (?, ?, ?)",
            (voter_id, token_hash, signature)
        )
        conn.commit()
        cur.close()

    def get_token_by_voter(self, voter_id):
        """Get token data for a specific voter"""
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM tokens WHERE voter_id = ?",
            (voter_id,)
        )
        row = cur.fetchone()
        cur.close()
        
        if row:
            return {
                "voter_id": row["voter_id"],
                "token_hash": row["token_hash"],
                "signature": row["signature"]
            }
        return None

    def token_exists(self, voter_id):
        """Check if a voter already has a token"""
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM tokens WHERE voter_id = ?",
            (voter_id,)
        )
        count = cur.fetchone()[0]
        cur.close()
        return count > 0