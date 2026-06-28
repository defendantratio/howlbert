import sqlite3
c=sqlite3.connect("fable.db")
cur=c.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables=[r[0] for r in cur.fetchall()]
print("tables", tables)
if "packs" in tables:
    cur.execute("SELECT count(*) FROM packs")
    print("packs", cur.fetchone()[0])
if "items" in tables:
    cur.execute("SELECT count(*) FROM items")
    print("items", cur.fetchone()[0])
c.close()
