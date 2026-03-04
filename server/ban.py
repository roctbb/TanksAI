import sqlite3
import sys
from config import db_path

if len(sys.argv) == 2:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("UPDATE players SET state = 'waiting' WHERE id = ?", (sys.argv[1], ))

    print("done")

    conn.commit()