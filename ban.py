import sqlite3
import sys

if len(sys.argv) == 2:

    conn = sqlite3.connect('tanks.sqlite')
    c = conn.cursor()
    c.execute("UPDATE players SET state = 'waiting' WHERE id = ?", (sys.argv[1], ))

    print("done")

    conn.commit()