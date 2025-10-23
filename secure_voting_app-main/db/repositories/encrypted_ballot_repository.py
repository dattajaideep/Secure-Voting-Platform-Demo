# db/repositories/encrypted_ballot_repository.py
"""
Repository for encrypted ballot storage and retrieval.

Handles persistence of end-to-end encrypted votes before decryption
and processing by the voting authority.
"""

from db.connection import get_conn
from utils.logger import add_log


class EncryptedBallotRepository:
    """Manages encrypted ballot storage in the database."""
    
    def __init__(self):
        """Initialize the encrypted ballot repository."""
        self.conn = get_conn()
    
    def add_encrypted_ballot(self, transmission_id: str, nonce: str, 
                           ciphertext: str, tag: str, envelope_hash: str) -> int:
        """
        Store an encrypted ballot in the database.
        
        Args:
            transmission_id: Unique identifier for this transmission
            nonce: Hex-encoded nonce used in encryption
            ciphertext: Hex-encoded encrypted vote data
            tag: Hex-encoded GCM authentication tag
            envelope_hash: SHA-256 hash of the encrypted envelope
            
        Returns:
            int: The database ID of the stored encrypted ballot
            
        Raises:
            Exception: If transmission_id already exists or database error occurs
        """
        cur = self.conn.cursor()
        try:
            cur.execute("""
                INSERT INTO encrypted_ballots 
                (transmission_id, nonce, ciphertext, tag, envelope_hash)
                VALUES (?, ?, ?, ?, ?)
            """, (transmission_id, nonce, ciphertext, tag, envelope_hash))
            self.conn.commit()
            
            ballot_id = cur.lastrowid
            add_log(
                f"Encrypted ballot stored: transmission_id={transmission_id}, ballot_id={ballot_id}",
                "info"
            )
            return ballot_id
            
        except Exception as e:
            add_log(f"Error storing encrypted ballot: {str(e)}", "error")
            raise
    
    def get_encrypted_ballot(self, transmission_id: str) -> dict:
        """
        Retrieve an encrypted ballot by transmission ID.
        
        Args:
            transmission_id: The transmission ID of the ballot
            
        Returns:
            dict: Ballot record or None if not found
        """
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, transmission_id, nonce, ciphertext, tag, 
                   envelope_hash, received_at
            FROM encrypted_ballots
            WHERE transmission_id = ?
        """, (transmission_id,))
        
        row = cur.fetchone()
        return dict(row) if row else None
    
    def get_all_encrypted_ballots(self, limit: int = None, offset: int = 0) -> list:
        """
        Retrieve all encrypted ballots.
        
        Args:
            limit: Maximum number of ballots to retrieve
            offset: Number of ballots to skip
            
        Returns:
            list: List of encrypted ballot records
        """
        cur = self.conn.cursor()
        
        if limit is not None:
            cur.execute("""
                SELECT id, transmission_id, nonce, ciphertext, tag,
                       envelope_hash, received_at
                FROM encrypted_ballots
                ORDER BY received_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
        else:
            cur.execute("""
                SELECT id, transmission_id, nonce, ciphertext, tag,
                       envelope_hash, received_at
                FROM encrypted_ballots
                ORDER BY received_at DESC
            """)
        
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    
    def get_encrypted_ballots_count(self) -> int:
        """
        Get the total count of encrypted ballots received.
        
        Returns:
            int: Total count of encrypted ballots
        """
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) as count FROM encrypted_ballots")
        row = cur.fetchone()
        return row['count'] if row else 0
    
    def verify_envelope_hash(self, transmission_id: str, computed_hash: str) -> bool:
        """
        Verify the integrity of a received encrypted envelope.
        
        Args:
            transmission_id: The transmission ID
            computed_hash: The hash computed from the received envelope
            
        Returns:
            bool: True if hashes match, False otherwise
        """
        ballot = self.get_encrypted_ballot(transmission_id)
        if not ballot:
            add_log(f"Envelope verification failed: transmission not found: {transmission_id}", "warning")
            return False
        
        stored_hash = ballot['envelope_hash']
        if stored_hash == computed_hash:
            add_log(f"Envelope integrity verified: {transmission_id}", "info")
            return True
        else:
            add_log(
                f"Envelope integrity check FAILED for {transmission_id}: "
                f"stored={stored_hash[:16]}..., computed={computed_hash[:16]}...",
                "error"
            )
            return False
    
    def delete_encrypted_ballot(self, transmission_id: str) -> bool:
        """
        Delete an encrypted ballot after successful decryption and processing.
        
        Args:
            transmission_id: The transmission ID to delete
            
        Returns:
            bool: True if deleted successfully
        """
        cur = self.conn.cursor()
        cur.execute("DELETE FROM encrypted_ballots WHERE transmission_id = ?", (transmission_id,))
        self.conn.commit()
        
        if cur.rowcount > 0:
            add_log(f"Encrypted ballot deleted after processing: {transmission_id}", "info")
            return True
        else:
            add_log(f"No encrypted ballot found to delete: {transmission_id}", "warning")
            return False
    
    def clear_all_encrypted_ballots(self) -> int:
        """
        Clear all encrypted ballots (for testing/reset purposes).
        
        Returns:
            int: Number of ballots deleted
        """
        cur = self.conn.cursor()
        cur.execute("DELETE FROM encrypted_ballots")
        self.conn.commit()
        
        count = cur.rowcount
        add_log(f"All encrypted ballots cleared: {count} records deleted", "warning")
        return count
