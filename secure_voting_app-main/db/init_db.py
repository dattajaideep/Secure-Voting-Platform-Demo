# db/init_db.py
from db.connection import get_conn
from utils.logger import add_log

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS voters (
            voter_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            has_token INTEGER DEFAULT 0,
            has_voted INTEGER DEFAULT 0
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
            token_value TEXT NOT NULL,
            issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(voter_id) REFERENCES voters(voter_id)
        )
    """)

    conn.commit()
    conn.close()
    add_log("Database tables initialized successfully", "info")

if __name__ == "__main__":
    init_db()
    print("Database created successfully")
