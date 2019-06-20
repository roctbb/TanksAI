import sqlite3

conn = sqlite3.connect('tanks.sqlite')
c = conn.cursor()
c.execute("UPDATE settings SET value = 'sandbox' WHERE param = 'mode';")
c.execute("UPDATE settings SET value = 20 WHERE param = 'max_health';")
c.execute("UPDATE settings SET value = 1 WHERE param = 'game_stop';")
c.execute("UPDATE settings SET value = 120 WHERE param = 'stop_ticks';")

conn.commit()