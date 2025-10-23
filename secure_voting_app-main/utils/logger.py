# utils/logger.py
import sqlite3
import os
import datetime

# Database lives in project root
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "voting.db")

def add_log(message, log_type="info"):
    """Writes a log entry directly into SQLite (no circular imports)."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Create logs table if it doesn't exist (safe call)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT,
                log_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute(
            "INSERT INTO logs (message, log_type, created_at) VALUES (?, ?, ?)",
            (message, log_type, timestamp)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Logger error: {e}")

    # Always print as backup
    print(f"[{timestamp}] ({log_type.upper()}) {message}")

