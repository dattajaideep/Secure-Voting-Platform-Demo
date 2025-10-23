# db/connection.py
import sqlite3
import os

# Database file stored locally in the project root
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "voting.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Enables dictionary-like access to rows
    return conn
