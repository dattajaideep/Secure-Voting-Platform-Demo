"""
Ballot Repository Module

Manages all ballot-related database operations including storage,
retrieval, and management of cast votes. Provides CRUD operations
for ballot records and logs all ballot-related activities.
"""

from db.connection import get_conn
from utils.logger import add_log
from typing import List, Dict, Any

class BallotRepository:
    def __init__(self):
        self.conn = get_conn()

    def add_ballot(self, candidate: str) -> None:
        """
        Add a new ballot record for a candidate.

        Args:
            candidate (str): The candidate name to record
        """
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO ballots (candidate)
            VALUES (?)
        """, (candidate,))
        self.conn.commit()
        add_log(f"Ballot cast for {candidate}", "info")

    def get_all_ballots(self) -> List[Dict[str, Any]]:
        """
        Retrieve all ballot records from the database.

        Returns:
            List[Dict[str, Any]]: List of ballot records as dictionaries
        """
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM ballots")
        rows = cur.fetchall()
        return [dict(r) for r in rows]

    def clear_ballots(self) -> None:
        """
        Clear all ballot records from the database.
        Logs the action for audit purposes.
        """
        cur = self.conn.cursor()
        cur.execute("DELETE FROM ballots")
        self.conn.commit()
        add_log("All ballots cleared", "warning")
 
