import sqlite3

def check_db():
    conn = sqlite3.connect("voting.db")
    cur = conn.cursor()

    print("\n== Tables in Database ==")
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cur.fetchall()]
    for t in tables:
        print("-", t)

    print("\n== Logs Preview ==")
    cur.execute("SELECT * FROM logs LIMIT 5;")
    for row in cur.fetchall():
        print(row)

    conn.close()

if __name__ == "__main__":
    check_db()
