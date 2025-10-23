# utils/logger.py
import sqlite3
import os
import datetime
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database lives in project root
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "voting.db")

# Logger configuration from .env
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'voting_platform.log')

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

def setup_logger(name: str = 'voting_platform'):
    """Setup application logger with file output"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        logger.addHandler(file_handler)
    
    return logger

# Initialize default logger
default_logger = setup_logger()

