import sqlite3

conn = sqlite3.connect('../data/tanks.sqlite')
c = conn.cursor()
c.execute("DELETE FROM players WHERE id != 52 AND id != 90")
c.execute("DELETE FROM statistics")
c.execute("DELETE FROM coins")
c.execute("DELETE FROM game")

conn.commit()