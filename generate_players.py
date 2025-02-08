players = 14

import sqlite3
import string
import random

def generate_random_sequence():
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=6))


conn = sqlite3.connect('./data/tanks.sqlite')
c = conn.cursor()

for i in range(players):
    random_key = generate_random_sequence()
    c.execute("INSERT INTO players (key) VALUES (?)", (random_key, ))
conn.commit()