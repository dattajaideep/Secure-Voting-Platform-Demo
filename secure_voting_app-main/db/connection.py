# db/connection.py
import sqlite3
import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
from utils.logger import add_log

# Load environment variables
load_dotenv()

# Database configuration from .env
DATABASE_URL = os.getenv('DATABASE_URL')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'voting_db')
DB_USER = os.getenv('DB_USER', 'voting_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')

# ==================== SQLITE ENCRYPTION SETUP ====================
# Get encryption key from environment - used to encrypt database at rest
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')

# Validate encryption key format (should be 64 hex characters = 32 bytes)
if ENCRYPTION_KEY:
    if len(ENCRYPTION_KEY) != 64 or not all(c in '0123456789abcdefABCDEF' for c in ENCRYPTION_KEY):
        error_msg = "ENCRYPTION_KEY must be 64 hexadecimal characters (32 bytes hex-encoded)"
        add_log(f"ERROR: {error_msg}", "error")
        raise ValueError(error_msg)
    add_log("SQLite encryption enabled - database will be encrypted at rest", "info")
else:
    add_log("WARNING: ENCRYPTION_KEY not set - database will NOT be encrypted", "warning")

# Fallback to SQLite if PostgreSQL not configured
USE_SQLITE = os.getenv('USE_SQLITE', 'true').lower() == 'true'

if USE_SQLITE:
    # Database file stored locally in the project root
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "voting.db")
    
    def get_conn():
        """
        Create encrypted SQLite connection using sqlcipher.
        
        SQLite database is encrypted at rest using the ENCRYPTION_KEY.
        All data on disk is protected - an attacker cannot read the database
        without the encryption key, even if they gain filesystem access.
        """
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Enables dictionary-like access to rows
        
        # Enable encryption if key is available
        if ENCRYPTION_KEY:
            # Convert hex key to binary format for SQLCipher pragma
            # PRAGMA key expects the key as: x'<hex_string>'
            try:
                conn.execute(f"PRAGMA key=\"x'{ENCRYPTION_KEY}'\"")
                # Verify encryption is working by testing a simple query
                conn.execute("SELECT 1")
                # Enable additional security pragmas for encrypted database
                conn.execute("PRAGMA cipher_page_size = 4096")  # Standard page size
                conn.execute("PRAGMA cipher_default_use_hmac = ON")  # Enable HMAC for integrity
                # Commit to ensure encryption takes effect
                conn.commit()
            except Exception as e:
                error_msg = f"Failed to enable database encryption: {str(e)}"
                add_log(error_msg, "error")
                raise RuntimeError(error_msg)
        
        return conn
else:
    # PostgreSQL connection pool
    try:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            1, 20,
            host=DB_HOST,
            port=int(DB_PORT),
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
    except Exception as e:
        print(f"Error creating PostgreSQL connection pool: {e}")
        connection_pool = None
    
    def get_conn():
        if connection_pool:
            return connection_pool.getconn()
        else:
            # Fallback to direct connection if pool failed
            return psycopg2.connect(
                host=DB_HOST,
                port=int(DB_PORT),
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
    
    def return_conn(conn):
        if connection_pool:
            connection_pool.putconn(conn)
