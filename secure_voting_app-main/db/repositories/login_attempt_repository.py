from db.connection import get_conn
from datetime import datetime, timedelta
from typing import Optional, Tuple
import time
import pytz

def make_aware(dt: datetime) -> datetime:
    """Convert naive datetime to UTC timezone-aware datetime"""
    if dt.tzinfo is None:
        return pytz.UTC.localize(dt)
    return dt

class LoginAttemptRepository:
    @staticmethod
    def create_table():
        """Create the login_attempts table if it doesn't exist and clean up invalid lockouts"""
        conn = get_conn()
        cur = conn.cursor()
        
        # Clean up any existing invalid lockouts
        current_time = datetime.now(pytz.UTC).replace(tzinfo=None, microsecond=0)
        max_lockout_time = current_time + timedelta(minutes=30)
        
        # Reset any lockouts that are too far in the future
        cur.execute("""
            UPDATE login_attempts 
            SET lockout_until = NULL, 
                attempt_count = 0
            WHERE lockout_until > ?
        """, (max_lockout_time.isoformat(' '),))
        
        conn.commit()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                attempt_count INTEGER DEFAULT 1,
                last_attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                lockout_until TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_attempts(email: str) -> Optional[Tuple[int, datetime, Optional[datetime]]]:
        """
        Get login attempt information for an email
        
        Returns:
            Tuple of (attempt_count, last_attempt_time, lockout_until)
            or None if no attempts found
        """
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT attempt_count, last_attempt_time, lockout_until
            FROM login_attempts 
            WHERE email = ?
        """, (email,))
        
        result = cur.fetchone()
        conn.close()
        
        if result:
            try:
                last_attempt = make_aware(datetime.fromisoformat(result[1].replace('Z', '')))
                lockout_until = (
                    make_aware(datetime.fromisoformat(result[2].replace('Z', '')))
                    if result[2] else None
                )
                return (result[0], last_attempt, lockout_until)
            except (ValueError, TypeError) as e:
                # If there's any issue parsing the dates, reset the record
                LoginAttemptRepository.reset_attempts(email)
                return None
        return None
    
    @staticmethod
    def reset_attempts(email: str):
        """Reset attempt count and clear lockout for an email"""
        conn = get_conn()
        cur = conn.cursor()
        
        # Store UTC time without timezone info in SQLite
        current_time = datetime.now(pytz.UTC).replace(tzinfo=None).isoformat(' ')
        
        cur.execute("""
            INSERT INTO login_attempts (email, attempt_count, last_attempt_time, lockout_until)
            VALUES (?, 0, ?, NULL)
            ON CONFLICT(email) DO UPDATE SET
                attempt_count = 0,
                last_attempt_time = ?,
                lockout_until = NULL
        """, (email, current_time, current_time))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def increment_attempts(email: str, lockout_duration: int = 0):
        """
        Increment attempt count and optionally set lockout time
        
        Args:
            email: User's email
            lockout_duration: Lockout duration in seconds (0 for no lockout)
        """
        conn = get_conn()
        cur = conn.cursor()
        
        # Use UTC time but store without timezone info in SQLite
        current_time = datetime.now(pytz.UTC).replace(tzinfo=None, microsecond=0)
        lockout_until = None
        
        if lockout_duration > 0:
            # Ensure lockout duration doesn't exceed the maximum
            lockout_duration = min(lockout_duration, 30 * 60)  # Max 30 minutes
            lockout_until = (current_time + timedelta(seconds=lockout_duration))
        
        # Convert to ISO format for SQLite storage
        current_time_str = current_time.isoformat(' ')
        lockout_until_str = lockout_until.isoformat(' ') if lockout_until else None
        
        cur.execute("""
            INSERT INTO login_attempts (email, attempt_count, last_attempt_time, lockout_until)
            VALUES (?, 1, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                attempt_count = attempt_count + 1,
                last_attempt_time = ?,
                lockout_until = ?
        """, (email, current_time_str, lockout_until_str, current_time_str, lockout_until_str))
        
        conn.commit()
        conn.close()