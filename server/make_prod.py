import sqlite3
from config import db_path

conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("UPDATE settings SET value = 'production' WHERE param = 'mode';")
c.execute("UPDATE settings SET value = 50 WHERE param = 'max_health';")
c.execute("UPDATE settings SET value = 0 WHERE param = 'game_stop';")
c.execute("UPDATE settings SET value = 300 WHERE param = 'stop_ticks';")

conn.commit()