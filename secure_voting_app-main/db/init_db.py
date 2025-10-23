# db/init_db.py
import sqlite3
from db.connection import get_conn
from utils.logger import add_log

# ==================== DATABASE ROLES DEFINITION ====================
# These roles define access permissions at the database level
DB_ROLES = {
    "admin": {
        "description": "Full database access - manages system configuration, users, and voting process",
        "permissions": {
            "voters": ["SELECT", "INSERT", "UPDATE", "DELETE"],
            "ballots": ["SELECT", "INSERT", "UPDATE", "DELETE"],
            "encrypted_ballots": ["SELECT", "INSERT", "UPDATE", "DELETE"],
            "tokens": ["SELECT", "INSERT", "UPDATE", "DELETE"],
            "logs": ["SELECT", "INSERT", "UPDATE", "DELETE"],
            "mixnet_proofs": ["SELECT", "INSERT", "UPDATE", "DELETE"],
            "login_attempts": ["SELECT", "INSERT", "UPDATE", "DELETE"],
            "db_roles": ["SELECT", "INSERT", "UPDATE", "DELETE"],
            "role_permissions": ["SELECT", "INSERT", "UPDATE", "DELETE"]
        }
    },
    "voter": {
        "description": "Limited access - voters can cast votes and view results",
        "permissions": {
            "voters": ["SELECT"],  # Read-only access to voter info
            "ballots": ["SELECT"],  # View available candidates
            "encrypted_ballots": ["INSERT", "SELECT"],  # Submit encrypted votes and check status
            "tokens": ["SELECT"],  # Verify token validity
            "logs": ["SELECT"],  # View audit logs (anonymized)
            "tally_results": ["SELECT"]  # View voting results
        }
    },
    "auditor": {
        "description": "Read-only access - reviews system logs and verifies integrity",
        "permissions": {
            "voters": ["SELECT"],  # View voter information
            "ballots": ["SELECT"],  # View ballot candidates
            "encrypted_ballots": ["SELECT"],  # Verify encrypted submissions
            "tokens": ["SELECT"],  # Verify token usage
            "logs": ["SELECT"],  # Full audit log access
            "mixnet_proofs": ["SELECT"],  # Verify mixnet integrity
            "login_attempts": ["SELECT"],  # Review login history
            "db_roles": ["SELECT"]  # View role definitions
        }
    }
}

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
        "encrypted_ballots": ["id", "transmission_id", "nonce", "ciphertext", "tag", "envelope_hash", "received_at"],
        "tokens": ["id", "voter_id", "token_hash", "signature", "issued_at"],
        "logs": ["id", "message", "log_type", "created_at"],
        "mixnet_proofs": ["id", "layer", "input_count", "output_count", "proof_hash"],
        "login_attempts": ["id", "email", "attempt_count", "last_attempt_time", "lockout_until", "created_at"],
        "db_roles": ["role_id", "role_name", "description"],
        "role_permissions": ["id", "role_id", "resource", "permission"]
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
    
    # Create encrypted ballots table for end-to-end encrypted votes
    cur.execute("""
        CREATE TABLE IF NOT EXISTS encrypted_ballots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transmission_id TEXT NOT NULL UNIQUE,
            nonce TEXT NOT NULL,
            ciphertext TEXT NOT NULL,
            tag TEXT NOT NULL,
            envelope_hash TEXT NOT NULL,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # --- CREATE DATABASE ROLES TABLES ---
    # Table to store role definitions
    cur.execute("""
        CREATE TABLE IF NOT EXISTS db_roles (
            role_id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Table to store role-permission mappings
    cur.execute("""
        CREATE TABLE IF NOT EXISTS role_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id INTEGER NOT NULL,
            resource TEXT NOT NULL,
            permission TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(role_id) REFERENCES db_roles(role_id) ON DELETE CASCADE,
            UNIQUE(role_id, resource, permission)
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
    
    # --- INITIALIZE DATABASE ROLES AND PERMISSIONS ---
    # Check if roles already exist
    cur.execute("SELECT COUNT(*) FROM db_roles")
    role_count = cur.fetchone()[0]
    
    if role_count == 0:
        # Insert roles
        for role_name, role_config in DB_ROLES.items():
            cur.execute(
                """INSERT INTO db_roles (role_name, description) 
                   VALUES (?, ?)""",
                (role_name, role_config["description"])
            )
            role_id = cur.lastrowid
            add_log(f"Created database role: {role_name}", "info")
            
            # Insert permissions for this role
            for resource, permissions in role_config["permissions"].items():
                for permission in permissions:
                    try:
                        cur.execute(
                            """INSERT INTO role_permissions (role_id, resource, permission) 
                               VALUES (?, ?, ?)""",
                            (role_id, resource, permission)
                        )
                    except sqlite3.IntegrityError:
                        # Permission already exists, skip
                        pass
            
            add_log(
                f"Initialized {len(role_config['permissions'])} resources with permissions for role '{role_name}'",
                "info"
            )
    else:
        add_log(f"Database roles already initialized ({role_count} roles found)", "info")

    conn.commit()
    conn.close()
    add_log("Database tables initialized and validated successfully", "info")
    
    # Final schema verification
    verify_schema_integrity()

if __name__ == "__main__":
    init_db()
    print("Database created successfully")