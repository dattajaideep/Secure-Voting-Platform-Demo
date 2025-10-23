# db/connection.py
import sqlite3
import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration from .env
DATABASE_URL = os.getenv('DATABASE_URL')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'voting_db')
DB_USER = os.getenv('DB_USER', 'voting_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')

# Fallback to SQLite if PostgreSQL not configured
USE_SQLITE = os.getenv('USE_SQLITE', 'true').lower() == 'true'

if USE_SQLITE:
    # Database file stored locally in the project root
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "voting.db")
    
    def get_conn():
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Enables dictionary-like access to rows
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
