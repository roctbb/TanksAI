import random
import string
import sqlite3

def getKey(N):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(N))

conn = sqlite3.connect('tanks.sqlite')
c = conn.cursor()
#c.execute("DELETE FROM players")
names = ['Savcha']
for name in names:
    key = getKey(8)
    print(name," - ", key)
    c.execute("INSERT INTO players (name, key, state) VALUES (?,?,?)", [name, key, "waiting"])

conn.commit();

'''
Crimson   4  3    4 4   15
Son       3  1  2   1  7    - II
Lizzy     2     1     3
Korol'    1       1   2
Saraj        2    2   4     - III
Kolobok      4  4   2  10
nik             3 3 3  9    - I
'''
