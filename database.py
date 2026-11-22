import sqlite3

conn = sqlite3.connect("sleep.db", check_same_thread=False)
cur = conn.cursor()

def init_db():
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT, coins INTEGER DEFAULT 100,
        bedtime TEXT DEFAULT '23:00', status TEXT DEFAULT 'awake',
        ping_ts REAL DEFAULT 0, warned INTEGER DEFAULT 0, rival_id INTEGER DEFAULT 0, bet INTEGER DEFAULT 0
    )""")
    conn.commit()

def get_user(uid, uname="Игрок"):
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (uid, uname))
        conn.commit()
        return get_user(uid, uname)
    return row

def update_field(uid, field, val):
    cur.execute(f"UPDATE users SET {field}=? WHERE user_id=?", (val, uid))
    conn.commit()

def find_rival(uid, bet):
    cur.execute("SELECT user_id FROM users WHERE user_id!=? AND rival_id=0 AND coins>=?", (uid, bet))
    res = cur.fetchone()
    return res[0] if res else None
