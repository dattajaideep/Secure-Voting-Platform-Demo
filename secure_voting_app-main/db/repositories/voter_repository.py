# db/repositories/voter_repository.py
from db.connection import get_conn
from utils.logger import add_log

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
