import sqlite3

conn = sqlite3.connect('../data/tanks.sqlite')
c = conn.cursor()
c.execute("UPDATE settings SET value = 'production' WHERE param = 'mode';")
c.execute("UPDATE settings SET value = 50 WHERE param = 'max_health';")
c.execute("UPDATE settings SET value = 0 WHERE param = 'game_stop';")
c.execute("UPDATE settings SET value = 300 WHERE param = 'stop_ticks';")

conn.commit()