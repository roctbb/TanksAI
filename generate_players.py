import sqlite3
import string
import random
from server.config import db_path

players = 14

def generate_random_sequence():
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=6))


conn = sqlite3.connect(db_path)
c = conn.cursor()

for i in range(players):
    random_key = generate_random_sequence()
    c.execute("INSERT INTO players (key) VALUES (?)", (random_key, ))
conn.commit()