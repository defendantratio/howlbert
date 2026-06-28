import os, sqlite3
from config import DB_PATH, BOT_DISPLAY_NAME
print("HOWLBERT_DB_PATH env:", os.getenv("HOWLBERT_DB_PATH"))
print("config.DB_PATH:", DB_PATH)
p = "fable.db"
print("exists", os.path.exists(p), "size", os.path.getsize(p) if os.path.exists(p) else None)
if os.path.exists(p):
    conn = sqlite3.connect(p)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [r[0] for r in cur.fetchall()]
    print("tables:", tables)
    conn.close()
