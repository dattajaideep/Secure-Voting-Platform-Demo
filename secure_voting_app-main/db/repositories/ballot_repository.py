# db/repositories/ballot_repository.py
from db.connection import get_conn
from utils.logger import add_log

class BallotRepository:
    def __init__(self):
        self.conn = get_conn()

    def add_ballot(self, candidate: str):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO ballots (candidate)
            VALUES (?)
        """, (candidate,))
        self.conn.commit()
        add_log(f"Ballot cast for {candidate}", "info")

    def get_all_ballots(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM ballots")
        rows = cur.fetchall()
        return [dict(r) for r in rows]

    def clear_ballots(self):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM ballots")
        self.conn.commit()
        add_log("All ballots cleared", "warning")

