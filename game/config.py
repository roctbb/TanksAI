import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

registration_enabled = bool(os.environ.get("REGISTRATION_ENABLED", True))
db_path = os.environ.get("DB_PATH", "/app/data/tanks.sqlite")
map_path = os.environ.get("MAP_PATH", "/app/data/map.txt")
