import sqlite3
from config import db_path

conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("DELETE FROM players WHERE id != 52 AND id != 90")
c.execute("DELETE FROM statistics")
c.execute("DELETE FROM coins")
c.execute("DELETE FROM game")

conn.commit()