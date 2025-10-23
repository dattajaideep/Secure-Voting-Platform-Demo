# db/init_db.py
from db.connection import get_conn
from utils.logger import add_log

def verify_schema_integrity():
    """
    Verify all tables have required columns.
    Raises RuntimeError if schema is invalid.
    """
    conn = get_conn()
    cur = conn.cursor()
    
    # Required schema: table -> list of required columns
    required_schema = {
        "voters": ["voter_id", "name", "has_token", "has_voted", "password_hash", "password_salt"],
        "ballots": ["ballot_id", "candidate"],
        "tokens": ["id", "voter_id", "token_hash", "signature", "issued_at"],
        "logs": ["id", "message", "log_type", "created_at"],
        "mixnet_proofs": ["id", "layer", "input_count", "output_count", "proof_hash"],
        "login_attempts": ["id", "email", "attempt_count", "last_attempt_time", "lockout_until", "created_at"]
    }
    
    for table_name, required_cols in required_schema.items():
        cur.execute(f"PRAGMA table_info({table_name})")
        table_info = cur.fetchall()
        actual_cols = [col[1] for col in table_info]
        
        for col in required_cols:
            if col not in actual_cols:
                conn.close()
                error_msg = f"Schema error: {table_name} missing column {col}"
                add_log(f"ERROR: {error_msg}", "error")
                raise RuntimeError(error_msg)
    
    conn.close()
    add_log("Schema integrity verified", "info")

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # --- SCHEMA MIGRATION: Check and fix existing tables ---
    
    # Check tokens table for old schema
    cur.execute("PRAGMA table_info(tokens)")
    tokens_info = cur.fetchall()
    tokens_needs_recreation = False
    
    if tokens_info:
        col_names = [col[1] for col in tokens_info]
        # If old schema exists or missing token_hash, drop and recreate
        if ("token_value" in col_names and "token_hash" not in col_names) or \
           "token_hash" not in col_names:
            cur.execute("DROP TABLE IF EXISTS tokens")
            add_log("Migrated tokens table schema (removed old structure)", "info")
            tokens_needs_recreation = True
    
    # Check voters table for missing columns and update schema if needed
    cur.execute("PRAGMA table_info(voters)")
    voters_info = cur.fetchall()
    
    if voters_info:
        col_names = [col[1] for col in voters_info]
        
        # Add missing columns if they don't exist
        required_columns = {
            "has_token": "INTEGER DEFAULT 0",
            "has_voted": "INTEGER DEFAULT 0",
            "password_hash": "TEXT",
            "password_salt": "TEXT"
        }
        
        for col_name, col_type in required_columns.items():
            if col_name not in col_names:
                try:
                    cur.execute(f"ALTER TABLE voters ADD COLUMN {col_name} {col_type}")
                    add_log(f"Added {col_name} column to voters", "info")
                except Exception as e:
                    add_log(f"Error adding column {col_name}: {str(e)}", "error")
                    raise RuntimeError(f"Failed to add column {col_name} to voters table")
    else:
        # If voters table doesn't exist, it will be created with all columns in the CREATE TABLE statement below
        add_log("Voters table not found, will be created with full schema", "info")
    
    # Check ballots table for correct schema
    cur.execute("PRAGMA table_info(ballots)")
    ballots_info = cur.fetchall()
    if ballots_info:
        col_names = [col[1] for col in ballots_info]
        # If ballots table has incorrect schema, drop and recreate
        if "ballot_id" not in col_names or "candidate" not in col_names:
            cur.execute("DROP TABLE IF EXISTS ballots")
            add_log("Migrated ballots table schema", "info")
    
    # Check logs table
    cur.execute("PRAGMA table_info(logs)")
    logs_info = cur.fetchall()
    if logs_info:
        col_names = [col[1] for col in logs_info]
        if "log_type" not in col_names:
            cur.execute("ALTER TABLE logs ADD COLUMN log_type TEXT DEFAULT 'info'")
            add_log("Added log_type column to logs", "info")
    
    # --- CREATE TABLES WITH LATEST SCHEMA ---
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS voters (
            voter_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            has_token INTEGER DEFAULT 0,
            has_voted INTEGER DEFAULT 0,
            password_hash TEXT,
            password_salt TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ballots (
            ballot_id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT,
            log_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS mixnet_proofs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            layer INTEGER,
            input_count INTEGER,
            output_count INTEGER,
            proof_hash TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voter_id TEXT NOT NULL,
            token_hash TEXT NOT NULL,
            signature TEXT NOT NULL,
            issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(voter_id) REFERENCES voters(voter_id)
        )
    """)
    
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
    
    # --- POST-CREATION VALIDATION ---
    # Verify tokens table has required columns
    cur.execute("PRAGMA table_info(tokens)")
    tokens_final = cur.fetchall()
    token_col_names = [col[1] for col in tokens_final]
    
    if "token_hash" not in token_col_names:
        add_log("ERROR: tokens table missing token_hash column after creation", "error")
        raise RuntimeError("Database schema error: tokens table missing token_hash column")
    
    if "signature" not in token_col_names:
        add_log("ERROR: tokens table missing signature column after creation", "error")
        raise RuntimeError("Database schema error: tokens table missing signature column")

    conn.commit()
    conn.close()
    add_log("Database tables initialized and validated successfully", "info")
    
    # Final schema verification
    verify_schema_integrity()

if __name__ == "__main__":
    init_db()
    print("Database created successfully")

if __name__ == "__main__":
    init_db()
    print("Database created successfully")