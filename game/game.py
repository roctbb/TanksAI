import sqlite3
import random
import time
from config import *
import os
import subprocess
import json
import tempfile
import pathlib
import shutil

NSJAIL = "/usr/local/bin/nsjail"
WORKDIR = pathlib.Path("/tmp/work")
WORKDIR.mkdir(parents=True, exist_ok=True)


def run_bot(bot_path, state, work):
    if sum(f.stat().st_size for f in work.rglob("*") if f.is_file()) > 8 * 1024 * 1024:
        return {"choice": "crash", "error": "Disk quota exceeded"}
    # Write input for bot
    input_file = work / "input.json"
    input_file.write_text(json.dumps(state))

    cmd = [
        NSJAIL,
        "--quiet",
        "--mode=once",
        "--time_limit=0.8",
        "--rlimit_cpu=1",
        "--rlimit_as=256",
        "--rlimit_nproc=2",
        "--disable_clone_newnet",

        # mount Python into workspace
        "--bindmount_ro=/usr/local:/usr/local",
        "--bindmount_ro=/lib:/lib",
        "--bindmount_ro=/lib64:/lib64",
        f"--bindmount={work}:/work",
        f"--bindmount_ro={bot_path}:/work/bot.py",
        "--bindmount_ro=/app/bot_runner.py:/work/bot_runner.py",
        "--tmpfs=/tmp:size=16M",

        "--cwd=/work",
        "--",
        "/usr/local/bin/python3",
        "/work/bot_runner.py",
    ]

    proc = None
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=1.2,
        )
        return json.loads(proc.stdout)
    except subprocess.TimeoutExpired:
        return {}
    except json.JSONDecodeError:
        return {"choice": "crash", "error": "Incorrect JSON"}
    except Exception:
        if not proc:
            return {"choice": "crash", "error": "Couldn't load process"}
        if proc.stdout and proc.stderr:
            return {
                "choice": "crash",
                "error": f"Stdout:\n{proc.stdout[:500]}\n\nStderr:\n{proc.stderr[:500]}",
            }
        elif proc.stdout:
            return {
                "choice": "crash",
                "error": f"Stdout:\n{proc.stdout[:500]}",
            }
        elif proc.stderr:
            return {
                "choice": "crash",
                "error": proc.stderr[:500],
            }
        else:
            return {
                "choice": "crash",
                "error": "No stdout/stderr",
            }


def make_testing():
    # работа с m файлами
    folder = './bots'
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path) and file_path.find(".m")!=-1:
                print(the_file)
                os.unlink(file_path)
        except Exception as e:
            print(e)

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # get settings
    c.execute("SELECT * FROM settings")
    result = c.fetchall()
    settings = dict()
    for string in result:
        settings[string[1]] = string[2]
    print(settings)
    # get bots
    # change to in game
    names = dict()
    c.execute("SELECT key, name FROM players WHERE state = 'ready'")
    result = c.fetchall()
    players = list()
    print("CURRENT PLAYERS:")
    for string in result:
        print(string[0]+" - "+string[1])
        players.append(string[0])
        names[string[0]] = string[1]
    print("")
    print("")

    # clear current state
    c.execute("DELETE FROM statistics")
    c.execute("DELETE FROM actions")
    c.execute("DELETE FROM game")
    c.execute("DELETE FROM coins")

    # make map
    # mainMap = [['.' for i in range(int(settings["height"]))] for j in range(int(settings["width"]))]
    with open(map_path) as map_file:
        map_data = map_file.read()
        mainMap = map_data.split('\n')
        for i in range(len(mainMap)):
            mainMap[i] = mainMap[i].split(' ')
        settings["height"] = len(mainMap[0])
        settings["width"] = len(mainMap)

        print("size: {0} x {1}".format(settings["width"], settings["height"]))

    healthMap = [[0 for i in range(int(settings["height"]))] for j in range(int(settings["width"]))]
    for i in range(len(mainMap)):
        for j in range(len(mainMap[0])):
            if mainMap[i][j] in ('#', '@'):
                healthMap[i][j] = -1

    history = {}

    coords = dict()
    health = dict()
    errors = dict()
    coins = dict()
    crashes = dict()
    lifeplayers = len(players)
    kills = dict()
    ticks = 0
    steps = dict()
    shots = dict()
    banlist = list()
    bot_workdirs = {}

    for player in players:
        coords[player] = dict()
        steps[player] = 0
        errors[player] = 0
        crashes[player] = 0
        shots[player] = 0
        health[player] = int(settings["max_health"])
        kills[player] = 0
        coins[player] = 0
        history[player]=[]
        x = random.randint(0, int(settings["width"])-1)
        y = random.randint(0, int(settings["height"])-1)
        while mainMap[x][y]!='.':
            x = random.randint(0, int(settings["width"])-1)
            y = random.randint(0, int(settings["height"])-1)
        mainMap[x][y] = player
        healthMap[x][y] = int(settings["max_health"])
        coords[player]["x"] = x
        coords[player]["y"] = y
        work = WORKDIR / player
        work.mkdir(parents=True, exist_ok=True)
        bot_workdirs[player] = work
        c.execute("INSERT INTO statistics (key) VALUES (?)", [player])
        c.execute("INSERT INTO game (key,x,y,life) VALUES (?,?,?,?)", [player, x, y, str(health[player])])
    c.execute("UPDATE settings SET value = ? WHERE param = ?", ["running", "game_state"])

    # coins
    for i in range(30):
        x = random.randint(0, int(settings["width"]) - 1)
        y = random.randint(0, int(settings["height"]) - 1)
        while mainMap[x][y] != '.':
            x = random.randint(0, int(settings["width"])-1)
            y = random.randint(0, int(settings["height"])-1)
        mainMap[x][y] = '@'
        healthMap[x][y] = 1
        c.execute("INSERT INTO coins (x,y) VALUES (?,?)", [x,y])
    conn.commit()
    while lifeplayers > int(settings['game_stop']):
        if int(settings['stop_ticks']) != 0 and ticks > int(settings['stop_ticks']):
            break
        print("current tick:"+str(ticks))
        choices = dict()
        ticks += 1

        historyMap = [[0 for i in range(int(settings["height"]))] for j in range(int(settings["width"]))]

        percentage_chance = 0.48
        if random.random() < percentage_chance:
            x = random.randint(0, int(settings["width"]) - 1)
            y = random.randint(0, int(settings["height"]) - 1)
            cc = 0
            while mainMap[x][y] != '.' and cc < 10:
                x = random.randint(0, int(settings["width"]) - 1)
                y = random.randint(0, int(settings["height"]) - 1)
                cc += 1
            if cc < 10:
                mainMap[x][y] = '@'
                healthMap[x][y] = 1
                c.execute("INSERT INTO coins (x,y) VALUES (?,?)", [x, y])
        conn.commit()

        for player in players:
            historyMap[coords[player]["x"]][coords[player]["y"]] = {"life": health[player], "history": history[player], "name": names[player]}

        for i in range(len(mainMap)):
            for j in range(len(mainMap[0])):
                if mainMap[i][j] == '#':
                    historyMap[i][j] = -1
                if mainMap[i][j] == '@':
                    historyMap[i][j] = 1

        timeout_flag = False
        for player in players:
            choices[player] = ""

            if player in banlist:
                continue

            c.execute("SELECT code FROM players WHERE key = ?", [player])
            code = c.fetchone()
            try:
                code = code[0].decode('utf8')
            except Exception as e:
                print("Error with", player, ": ", e)
                try:
                    code = code[0]
                except Exception as e:
                    print("Agein error with", player, ": ", e)
                    code = ""

            print(f"Now running: {player} ({names[player]})")

            with tempfile.NamedTemporaryFile(
                    mode="w",
                    suffix=".py",
                    delete=False,
            ) as bot_file:
                bot_file.write(code)
                bot_path = pathlib.Path(bot_file.name).resolve()

            try:
                result = run_bot(bot_path, (int(coords[player]["x"]), int(coords[player]["y"]), historyMap),
                                 bot_workdirs[player])
            finally:
                # Always clean up
                try:
                    bot_path.unlink()
                except OSError:
                    pass

            lerror = ""

            if 'choice' not in result:
                choices[player] = "crash"
                lerror = "timeout"
                timeout_flag = True
            elif 'error' in result:
                choices[player] = "crash"
                lerror = result['error']
            else:
                choices[player] = result['choice']

            if choices[player] == "crash":
                print(player+" ("+names[player]+") has crashed :( :"+lerror)
                history[player].append("crash")
                crashes[player]+=1
                c.execute("INSERT INTO actions (key, value) VALUES (?, ?)", [player, choices[player]])
                c.execute(
                    "UPDATE statistics SET crashes = ? WHERE key = ?",
                    [str(crashes[player]), player])
                c.execute(
                    "UPDATE statistics SET lastCrash = ? WHERE key = ?",
                    [lerror, player])
        conn.commit()

        #print(historyMap)
        for player in players:
            if player in banlist:
                continue
            if choices[player]=="go_up":
                steps[player]+=1
                if int(coords[player]["y"]) > 0 and mainMap[coords[player]["x"]][coords[player]["y"] - 1] in ('.', '@'):
                    if mainMap[coords[player]["x"]][coords[player]["y"] - 1] == '@':
                        coins[player] += 1
                    mainMap[coords[player]["x"]][coords[player]["y"]] = '.'
                    healthMap[coords[player]["x"]][coords[player]["y"]] = 0
                    coords[player]["y"] -= 1
                    mainMap[coords[player]["x"]][coords[player]["y"]] = player
                    healthMap[coords[player]["x"]][coords[player]["y"]] = health[player]
                    c.execute("UPDATE game SET y = ? WHERE key = ?", [str(coords[player]["y"]), player])
                    c.execute(
                        "DELETE FROM coins WHERE x = ? AND y = ?",
                        [coords[player]["x"], coords[player]["y"]])
            if choices[player] == "go_down":
                steps[player] += 1
                if int(coords[player]["y"]) < int(settings["height"]) - 1 and mainMap[coords[player]["x"]][coords[player]["y"]+1] in ('.', '@'):
                    if mainMap[coords[player]["x"]][coords[player]["y"] + 1] == '@':
                        coins[player] += 1
                    mainMap[coords[player]["x"]][coords[player]["y"]] = '.'
                    healthMap[coords[player]["x"]][coords[player]["y"]] = 0
                    coords[player]["y"] += 1
                    mainMap[coords[player]["x"]][coords[player]["y"]] = player
                    healthMap[coords[player]["x"]][coords[player]["y"]] = health[player]
                    c.execute("UPDATE game SET y = ? WHERE key = ?", [str(coords[player]["y"]), player])
                    c.execute(
                        "DELETE FROM coins WHERE x = ? AND y = ?",
                        [coords[player]["x"], coords[player]["y"]])
            if choices[player] == "go_left":
                steps[player] += 1
                if int(coords[player]["x"]) > 0 and mainMap[int(coords[player]["x"]) -1][coords[player]["y"]] in ('.', '@'):
                    if mainMap[coords[player]["x"]-1][coords[player]["y"]] == '@':
                        coins[player] += 1
                    mainMap[coords[player]["x"]][coords[player]["y"]] = '.'
                    healthMap[coords[player]["x"]][coords[player]["y"]] = 0
                    coords[player]["x"] -= 1
                    mainMap[coords[player]["x"]][coords[player]["y"]] = player
                    healthMap[coords[player]["x"]][coords[player]["y"]] = health[player]
                    c.execute("UPDATE game SET x = ? WHERE key = ?", [str(coords[player]["x"]), player])
                    c.execute(
                        "DELETE FROM coins WHERE x = ? AND y = ?",
                        [coords[player]["x"], coords[player]["y"]])
            if choices[player] == "go_right":
                steps[player] += 1
                if int(coords[player]["x"]) < int(settings["width"]) - 1 and mainMap[int(coords[player]["x"])+1][coords[player]["y"]] in ('.', '@'):
                    if mainMap[coords[player]["x"]+1][coords[player]["y"]] == '@':
                        coins[player] += 1
                    mainMap[coords[player]["x"]][coords[player]["y"]] = '.'
                    healthMap[coords[player]["x"]][coords[player]["y"]] = 0
                    coords[player]["x"]+=1
                    mainMap[coords[player]["x"]][coords[player]["y"]] = player
                    healthMap[coords[player]["x"]][coords[player]["y"]] = health[player]
                    c.execute("UPDATE game SET x = ? WHERE key = ?", [str(coords[player]["x"]), player])
                    c.execute(
                        "DELETE FROM coins WHERE x = ? AND y = ?",
                        [coords[player]["x"], coords[player]["y"]])
            if choices[player]=="go_up" or choices[player] == "go_down" or choices[player] == "go_left" or choices[player] == "go_right" or  choices[player] == "fire_up" or choices[player] == "fire_down" or choices[player] == "fire_left" or choices[player] == "fire_right" or choices[player] == "crash":
                c.execute("INSERT INTO actions (key, value) VALUES (?, ?)", [player, choices[player]])
                history[player].append(choices[player])
            else:
                print(player+" ("+names[player]+") sent incorrect command: "+str(choices[player]))
                errors[player] += 1
                history[player].append("error")
            #db record
        for player in players:
            if player in banlist:
                continue
            px = coords[player]["x"]
            py = coords[player]["y"]
            if choices[player] == "fire_up":
                shots[player] += 1
                for y in range(py-1, -1, -1):
                    if mainMap[px][y] == '#':
                        break
                    if mainMap[px][y] not in ('.', '@'):
                        hit_player = mainMap[px][y]

                        health[hit_player]-=1
                        healthMap[px][y] -= 1

                        kills[player]+=1

                        '''
                        print(player + " (" + str(health[player]) + ") hits " + str(hit_player) + " (" + str(
                            health[hit_player]) + ")" + " [" + str(px) + " ," + str(py) + "] -> [" + str(px) + ", " + str(
                            y) + "] " + choices[player])
                            '''

                        c.execute("UPDATE game SET life = ? WHERE key = ?", [str(health[hit_player]), hit_player])
                        break
            if choices[player] == "fire_down":
                shots[player] += 1
                for y in range(py+1, int(settings["height"])):
                    if mainMap[px][y] == '#':
                        break
                    if mainMap[px][y] not in ('.', '@'):
                        hit_player = mainMap[px][y]

                        health[hit_player] -= 1
                        healthMap[px][y] -= 1

                        kills[player] += 1

                        print(player + " ("+str(health[player])+") hits " + str(hit_player) + " (" + str(
                            health[hit_player]) + ")" + " [" + str(px) + " ," + str(py) + "] -> ["+str(px)+", "+str(y)+"] " + choices[player])



                        c.execute("UPDATE game SET life = ? WHERE key = ?", [str(health[hit_player]), hit_player])
                        break
            if choices[player] == "fire_left":
                shots[player] += 1
                for x in range(px-1, -1, -1):
                    if mainMap[x][py] == '#':
                        break
                    if mainMap[x][py] not in ('.', '@'):
                        hit_player = mainMap[x][py]

                        health[hit_player] -= 1
                        healthMap[x][py] -= 1

                        kills[player] += 1

                        print(player + " (" + str(health[player]) + ") hits " + str(hit_player) + " (" + str(
                            health[hit_player]) + ")" + " [" + str(px) + " ," + str(py) + "] -> [" + str(x) + ", " + str(
                            py) + "] " + choices[player])

                        c.execute("UPDATE game SET life = ? WHERE key = ?", [str(health[hit_player]), hit_player])
                        break
            if choices[player] == "fire_right":
                shots[player] += 1
                for x in range(px+1, int(settings["width"])):
                    if mainMap[x][py] == '#':
                        break
                    if mainMap[x][py] not in ('.', '@'):
                        hit_player = mainMap[x][py]

                        health[hit_player] -= 1
                        healthMap[x][py] -= 1

                        kills[player] += 1

                        print(player + " (" + str(health[player]) + ") hits " + str(hit_player) + " (" + str(
                            health[hit_player]) + ")" + " [" + str(px) + " ," + str(py) + "] -> [" + str(x) + ", " + str(
                            py) + "] " + choices[player])

                        c.execute("UPDATE game SET life = ? WHERE key = ?", [str(health[hit_player]), hit_player])
                        break

            if choices[player] == "fire_up" or choices[player] == "fire_down" or choices[player] == "fire_left" or choices[player] == "fire_right":
                c.execute(
                    "UPDATE statistics SET kills = ? WHERE key = ?", [str(kills[player]), player])
                #print(player + " sent "+choices[player])

                # db record

            if int(health[player])>0:
                c.execute(
                    "UPDATE statistics SET lifetime = ? WHERE key = ?",
                    [str(ticks), player])
                c.execute(
                    "UPDATE statistics SET shots = ? WHERE key = ?",
                    [str(shots[player]), player])
                c.execute(
                    "UPDATE statistics SET coins = ? WHERE key = ?",
                    [str(coins[player]), player])
                c.execute(
                    "UPDATE statistics SET steps = ? WHERE key = ?",
                    [str(steps[player]), player])
                c.execute(
                    "UPDATE statistics SET errors = ? WHERE key = ?",
                    [str(errors[player]), player])

            conn.commit()

        remove_list = []
        for hit_player in players:
            #print(hit_player+" "+str(health[hit_player])+" - check")
            if health[hit_player] <= 0:
                mainMap[coords[hit_player]['x']][coords[hit_player]['y']] = '.'
                healthMap[coords[hit_player]['x']][coords[hit_player]['y']] = 0
                health[hit_player] = 0
                lifeplayers -= 1
                print(hit_player + " is dead!")
                remove_list.append(hit_player)
        for p in remove_list:
            players.remove(p)
        conn.commit()
        if not timeout_flag:
            time.sleep(0.5)

    c.execute("UPDATE settings SET value = ? WHERE param = ?", ["stop", "game_state"])

    conn.commit()

    for player in players:
        shutil.rmtree(bot_workdirs[player], ignore_errors=True)

    return settings


while 1:
    s = make_testing()
    if s['mode'] != 'sandbox':
        time.sleep(60)
        break
    time.sleep(3)










