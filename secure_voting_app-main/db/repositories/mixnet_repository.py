# db/repositories/mixnet_repository.py
from db.connection import get_conn
from utils.logger import add_log

class MixNetRepository:
    def save_proof(self, proof: dict):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO mixnet_proofs (layer, input_count, output_count, proof_hash)
            VALUES (?, ?, ?, ?)
        """, (
            proof["layer"],
            proof["inputCount"],
            proof["outputCount"],
            proof["proof"]
        ))
        conn.commit()
        conn.close()
        add_log(f"MixNet proof saved for layer {proof['layer']}", "info")

