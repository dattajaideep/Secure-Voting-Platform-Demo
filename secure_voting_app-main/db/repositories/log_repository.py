# db/repositories/log_repository.py
from db.connection import get_conn

class LogRepository:
    def __init__(self):
        self.conn = get_conn()

    def add_log(self, message, log_type):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO logs (message, log_type)
            VALUES (?, ?)
        """, (message, log_type))
        self.conn.commit()

    def get_all_logs(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM logs ORDER BY created_at DESC")
        rows = cur.fetchall()
        return [dict(r) for r in rows]
