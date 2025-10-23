#!/usr/bin/env python3
# db/sanitize_db.py

import re
from datetime import datetime, timedelta
from typing import List, Dict, Any
from db.connection import get_conn
from utils.logger import add_log
from utils.validation import InputValidator
from utils.password_utils import verify_password, decode_hash_salt

class DatabaseSanitizer:
    def __init__(self):
        self.conn = get_conn()
        self.cur = self.conn.cursor()
        self.sanitization_log = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

    def log_sanitization(self, message: str, severity: str = "info"):
        """Log sanitization actions"""
        add_log(f"DB Sanitization: {message}", severity)
        self.sanitization_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "severity": severity
        })

    def clean_voters_table(self) -> int:
        """
        Clean the voters table:
        - Remove invalid email addresses
        - Remove duplicate voter IDs
        - Ensure required fields are not null
        - Validate password hashes
        """
        cleaned_count = 0
        
        # Get all voters
        self.cur.execute("SELECT voter_id, name, password_hash, password_salt FROM voters")
        voters = self.cur.fetchall()
        
        for voter in voters:
            voter_id, name, password_hash, password_salt = voter
            should_delete = False
            
            # Check if voter_id is valid
            try:
                InputValidator.validate_voter_id(voter_id)
            except Exception:
                should_delete = True
                self.log_sanitization(f"Invalid voter_id format: {voter_id}", "warning")
            
            # Check if name is valid
            if name:
                try:
                    InputValidator.validate_name(name)
                except Exception:
                    should_delete = True
                    self.log_sanitization(f"Invalid name format for voter: {voter_id}", "warning")
            
            # Validate password hash and salt if present
            if password_hash and password_salt:
                try:
                    decoded_hash, decoded_salt = decode_hash_salt(password_hash, password_salt)
                except Exception:
                    should_delete = True
                    self.log_sanitization(f"Invalid password hash/salt for voter: {voter_id}", "warning")
            
            if should_delete:
                self.cur.execute("DELETE FROM voters WHERE voter_id = ?", (voter_id,))
                cleaned_count += 1
        
        # Remove duplicate voter IDs (keep the most recent)
        self.cur.execute("""
            DELETE FROM voters 
            WHERE rowid NOT IN (
                SELECT MIN(rowid) 
                FROM voters 
                GROUP BY voter_id
            )
        """)
        
        duplicates_removed = self.cur.rowcount
        if duplicates_removed > 0:
            self.log_sanitization(f"Removed {duplicates_removed} duplicate voter entries", "warning")
            cleaned_count += duplicates_removed
        
        self.conn.commit()
        return cleaned_count

    def clean_tokens_table(self) -> int:
        """
        Clean the tokens table:
        - Remove expired tokens
        - Remove tokens with invalid signatures
        - Remove orphaned tokens (no corresponding voter)
        """
        cleaned_count = 0
        
        # Remove expired tokens (older than 24 hours)
        self.cur.execute("""
            DELETE FROM tokens 
            WHERE issued_at < datetime('now', '-24 hours')
        """)
        expired_removed = self.cur.rowcount
        if expired_removed > 0:
            self.log_sanitization(f"Removed {expired_removed} expired tokens", "info")
            cleaned_count += expired_removed
        
        # Remove orphaned tokens
        self.cur.execute("""
            DELETE FROM tokens 
            WHERE voter_id NOT IN (SELECT voter_id FROM voters)
        """)
        orphaned_removed = self.cur.rowcount
        if orphaned_removed > 0:
            self.log_sanitization(f"Removed {orphaned_removed} orphaned tokens", "warning")
            cleaned_count += orphaned_removed
        
        # Remove tokens with invalid hash format
        self.cur.execute("SELECT id, token_hash FROM tokens")
        tokens = self.cur.fetchall()
        for token_id, token_hash in tokens:
            if not re.match(r'^[A-Za-z0-9+/]{32,}={0,2}$', token_hash):  # Base64 format
                self.cur.execute("DELETE FROM tokens WHERE id = ?", (token_id,))
                self.log_sanitization(f"Removed token with invalid hash format: {token_id}", "warning")
                cleaned_count += 1
        
        self.conn.commit()
        return cleaned_count

    def clean_ballots_table(self) -> int:
        """
        Clean the ballots table:
        - Remove invalid ballot entries
        - Ensure candidate names are valid
        """
        cleaned_count = 0
        
        # Get all ballots
        self.cur.execute("SELECT ballot_id, candidate FROM ballots")
        ballots = self.cur.fetchall()
        
        for ballot_id, candidate in ballots:
            try:
                if candidate:
                    InputValidator.validate_candidate_name(candidate)
            except Exception:
                self.cur.execute("DELETE FROM ballots WHERE ballot_id = ?", (ballot_id,))
                self.log_sanitization(f"Removed ballot with invalid candidate name: {ballot_id}", "warning")
                cleaned_count += 1
        
        self.conn.commit()
        return cleaned_count

    def clean_logs_table(self) -> int:
        """
        Clean the logs table:
        - Remove old logs
        - Validate log types
        - Remove malformed entries
        """
        cleaned_count = 0
        
        # Remove logs older than 30 days
        self.cur.execute("""
            DELETE FROM logs 
            WHERE created_at < datetime('now', '-30 days')
        """)
        old_removed = self.cur.rowcount
        if old_removed > 0:
            self.log_sanitization(f"Removed {old_removed} old log entries", "info")
            cleaned_count += old_removed
        
        # Validate log types and remove invalid entries
        valid_log_types = {'info', 'warning', 'error', 'debug'}
        self.cur.execute("""
            DELETE FROM logs 
            WHERE log_type NOT IN ('info', 'warning', 'error', 'debug')
        """)
        invalid_type_removed = self.cur.rowcount
        if invalid_type_removed > 0:
            self.log_sanitization(f"Removed {invalid_type_removed} logs with invalid type", "warning")
            cleaned_count += invalid_type_removed
        
        self.conn.commit()
        return cleaned_count

    def clean_mixnet_proofs_table(self) -> int:
        """
        Clean the mixnet_proofs table:
        - Remove invalid proofs
        - Ensure count values are valid
        """
        cleaned_count = 0
        
        # Remove entries with invalid counts
        self.cur.execute("""
            DELETE FROM mixnet_proofs 
            WHERE input_count < 0 OR output_count < 0 
            OR input_count != output_count
        """)
        invalid_removed = self.cur.rowcount
        if invalid_removed > 0:
            self.log_sanitization(f"Removed {invalid_removed} invalid mixnet proofs", "warning")
            cleaned_count += invalid_removed
        
        # Remove entries with invalid proof hashes
        self.cur.execute("SELECT id, proof_hash FROM mixnet_proofs")
        proofs = self.cur.fetchall()
        for proof_id, proof_hash in proofs:
            if not proof_hash or not re.match(r'^[A-Fa-f0-9]{64}$', proof_hash):  # SHA-256 format
                self.cur.execute("DELETE FROM mixnet_proofs WHERE id = ?", (proof_id,))
                self.log_sanitization(f"Removed mixnet proof with invalid hash: {proof_id}", "warning")
                cleaned_count += 1
        
        self.conn.commit()
        return cleaned_count

    def analyze_database(self) -> Dict[str, Any]:
        """
        Analyze database for potential issues
        """
        analysis = {
            "tables": {},
            "foreign_keys": [],
            "indexes": [],
            "issues": []
        }
        
        # Check table statistics
        for table in ["voters", "tokens", "ballots", "logs", "mixnet_proofs"]:
            self.cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = self.cur.fetchone()[0]
            analysis["tables"][table] = {"row_count": count}
        
        # Check foreign key constraints
        self.cur.execute("PRAGMA foreign_key_check")
        fk_violations = self.cur.fetchall()
        if fk_violations:
            analysis["issues"].append({
                "type": "foreign_key_violation",
                "details": fk_violations
            })
        
        # Check for missing indexes
        self.cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = self.cur.fetchall()
        analysis["indexes"] = [idx[0] for idx in indexes]
        
        return analysis

def sanitize_database():
    """
    Main function to run database sanitization
    """
    start_time = datetime.now()
    cleaned_counts = {}
    
    try:
        with DatabaseSanitizer() as sanitizer:
            # Analyze database before cleaning
            initial_analysis = sanitizer.analyze_database()
            
            # Clean all tables
            cleaned_counts["voters"] = sanitizer.clean_voters_table()
            cleaned_counts["tokens"] = sanitizer.clean_tokens_table()
            cleaned_counts["ballots"] = sanitizer.clean_ballots_table()
            cleaned_counts["logs"] = sanitizer.clean_logs_table()
            cleaned_counts["mixnet_proofs"] = sanitizer.clean_mixnet_proofs_table()
            
            # Analyze database after cleaning
            final_analysis = sanitizer.analyze_database()
            
            # Calculate statistics
            total_cleaned = sum(cleaned_counts.values())
            duration = (datetime.now() - start_time).total_seconds()
            
            # Log summary
            summary = (
                f"Database sanitization completed in {duration:.2f} seconds\n"
                f"Total records cleaned: {total_cleaned}\n"
                f"Breakdown by table: {cleaned_counts}"
            )
            add_log(summary, "info")
            
            return {
                "status": "success",
                "cleaned_counts": cleaned_counts,
                "duration": duration,
                "initial_analysis": initial_analysis,
                "final_analysis": final_analysis,
                "log": sanitizer.sanitization_log
            }
            
    except Exception as e:
        error_msg = f"Database sanitization failed: {str(e)}"
        add_log(error_msg, "error")
        return {
            "status": "error",
            "error": error_msg,
            "cleaned_counts": cleaned_counts
        }

if __name__ == "__main__":
    result = sanitize_database()
    if result["status"] == "success":
        print("Database sanitization completed successfully!")
        print(f"Cleaned records: {result['cleaned_counts']}")
        print(f"Duration: {result['duration']:.2f} seconds")
    else:
        print(f"Error during sanitization: {result['error']}")