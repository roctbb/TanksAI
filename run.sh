#!/usr/bin/env bash
python3 game.py >> /dev/null 2&>1 & disown
python3 server.py >> /dev/null 2&>1 & disown