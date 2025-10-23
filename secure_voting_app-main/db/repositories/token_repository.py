# db/repositories/token_repository.py
from db.connection import get_conn

class TokenRepository:
    def add_token(self, voter_id: str, token_hash: str, signature: str):
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO tokens(voter_id, token_hash, signature)
                VALUES (%s, %s, %s)
                ON CONFLICT (voter_id) DO NOTHING
            """, (voter_id, token_hash, signature))
        conn.commit()
        conn.close()

    def get_token_by_voter(self, voter_id: str):
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM tokens WHERE voter_id=%s", (voter_id,))
            token = cur.fetchone()
        conn.close()
        return token
