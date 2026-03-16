import sqlite3
import random
import time
import sys
import os
import importlib as imp
import traceback
import multiprocessing
multiprocessing.set_start_method('fork')
from multiprocessing import Process, Queue, Manager
import ast
from config import *

def is_code_safe(code):
    # Запрещенные узлы AST
    forbidden = {
        # Запрещенные функции
        'eval': "Использование eval запрещено",
        'exec': "Использование exec запрещено",
        'open': "Использование open запрещено",
        # Запрещенные модули
        'os': "Импорт модуля os запрещен",
        'subprocess': "Использование subprocess запрещено",
        'socket': "Использование socket запрещено",
        'requests': "Использование requests запрещено",
        'http.client': "Использование http.client запрещено",
        'urllib': "Использование urllib запрещено",
        'pathlib': 'Использование pathlib запрещено',
        '__import__': 'Использование pathlib запрещено',
    }

    class SafeCodeChecker(ast.NodeVisitor):
        def visit_Call(self, node):
            # Проверяем вызовы функций
            if isinstance(node.func, ast.Name) and node.func.id in forbidden:
                raise ValueError(forbidden[node.func.id])
            self.generic_visit(node)

        def visit_Import(self, node):
            # Проверяем импорты модулей
            for alias in node.names:
                if alias.name in forbidden:
                    raise ValueError(forbidden[alias.name])
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            # Проверяем импорты из модулей
            if node.module in forbidden:
                raise ValueError(forbidden[node.module])
            for alias in node.names:
                if f"{node.module}.{alias.name}" in forbidden:
                    raise ValueError(forbidden[f"{node.module}.{alias.name}"])
            self.generic_visit(node)

        def visit_Expr(self, node):
            # Проверяем выражения, такие как eval и exec
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
                if node.value.func.id in ['eval', 'exec']:
                    raise ValueError(forbidden[node.value.func.id])
            self.generic_visit(node)

    try:
        # Парсим код в AST
        tree = ast.parse(code)
        # Проверяем код на безопасность
        SafeCodeChecker().visit(tree)
        return True
    except Exception as e:
        print(f"Ошибка: {e}")
        return False
        

def apply_damage(hit_player, damage, health, shield, choices, healthMap, x, y):
    if choices.get(hit_player) == "shield" and shield[hit_player] > 0:
        absorbed = min(damage, shield[hit_player])
        shield[hit_player] -= absorbed
        damage -= absorbed
    health[hit_player] -= damage
    healthMap[x][y] -= damage
    return damage


def wrapper(func, x, y, field, rv):
    try:
        result = func(x,y,field)
        rv['choice']= result
    except Exception as e:
        rv['choice'] = "crash"
        error_msg = traceback.format_exc()
        # Скрываем ключ игрока из traceback
        import re
        error_msg = re.sub(r'bots/bot\d+\.py', 'bots/bot.py', error_msg)
        rv['error'] = str(e) + " " + error_msg

def make_testing():
    #работа с m файлами
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

    #get settings
    c.execute("SELECT * FROM settings")
    result = c.fetchall()
    settings = dict()
    for string in result:
        settings[string[1]] = string[2]
    print(settings)
    #get bots
    #change to in game
    names = dict()
    c.execute("SELECT id, key, name FROM players WHERE state = 'ready'")
    result = c.fetchall()
    players = list()
    bot_files = dict()
    print("CURRENT PLAYERS:")
    for string in result:
        print(string[1]+" - "+string[2])
        players.append(string[1])
        names[string[1]]=string[2]
        bot_files[string[1]] = "bot{}".format(string[0])
    print("")
    print("")

    #clear current state
    c.execute("DELETE FROM statistics")
    c.execute("DELETE FROM actions")
    c.execute("DELETE FROM game")
    c.execute("DELETE FROM coins")



    #make map
    #mainMap = [['.' for i in range(int(settings["height"]))] for j in range(int(settings["width"]))]
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
    shield = dict()
    banlist = list()



    for player in players:
        coords[player] = dict()
        steps[player] = 0
        errors[player] = 0
        crashes[player] = 0
        shots[player] = 0
        health[player] = int(settings["max_health"])
        shield[player] = int(settings["max_health"]) // 2
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
        coords[player]["x"]=x
        coords[player]["y"] =y
        c.execute("INSERT INTO statistics (key) VALUES (?)", [player])
        c.execute("INSERT INTO game (key,x,y,life,shield) VALUES (?,?,?,?,?)", [player,x,y, str(health[player]), str(shield[player])])
    c.execute("UPDATE settings SET value = ? WHERE param = ?", ["running", "game_state"])

    #coins
    for i in range(30):
        x = random.randint(0, int(settings["width"]) - 1)
        y = random.randint(0, int(settings["height"]) - 1)
        while mainMap[x][y]!='.':
            x = random.randint(0, int(settings["width"])-1)
            y = random.randint(0, int(settings["height"])-1)
        mainMap[x][y] = '@'
        healthMap[x][y] = 1
        c.execute("INSERT INTO coins (x,y) VALUES (?,?)", [x,y])
    conn.commit()
    sys.path.append("bots/")
    while lifeplayers>int(settings['game_stop']):
        if int(settings['stop_ticks'])!=0 and ticks>int(settings['stop_ticks']):
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
            while mainMap[x][y] != '.' and cc<10:
                x = random.randint(0, int(settings["width"]) - 1)
                y = random.randint(0, int(settings["height"]) - 1)
                cc+=1
            if cc < 10:
                mainMap[x][y] = '@'
                healthMap[x][y] = 1
                c.execute("INSERT INTO coins (x,y) VALUES (?,?)", [x, y])
        conn.commit()

        for player in players:
            score = coins[player] * 50 + kills[player] * 20 + ticks - crashes[player] * 5
            historyMap[coords[player]["x"]][coords[player]["y"]] = {"life": health[player], "history": history[player], "name": names[player], "score": score, "shield": shield[player]}

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
                code = code[0].decode('utf8').replace('exit()', '').replace('telebot', '')
            except Exception as e:
                print("Error with", player, ": ", e)
                try:
                    code = code[0].replace('exit()', '').replace('telebot', '')
                except Exception as e:
                    print("Agein error with", player, ": ", e)
                    code = ""
            if not is_code_safe(code):
                code = ""
                print(code)
            output_file = open("./bots/" + bot_files[player] + ".py", 'w')
            output_file.write(code)
            output_file.close()

            lerror = ""

            try:
                module = __import__(bot_files[player], fromlist=["make_choice"])
                module = imp.reload(module)
                makeChoice = getattr(module, "make_choice")
                print("Now running:" +player+" ("+names[player]+")")

                manager = Manager()
                return_dict = manager.dict()

                thread = Process(
                    target=wrapper,
                    name="game_choice",
                    args=[makeChoice, int(coords[player]["x"]), int(coords[player]["y"]), historyMap, return_dict],
                )
                thread.start()
                thread.join(timeout=0.4)
                thread.terminate()




                if 'choice' not in return_dict:
                    choices[player] = "crash"
                    lerror = "timeout"
                    timeout_flag = True
                elif 'error' in return_dict:
                    choices[player] = "crash"
                    lerror = return_dict['error']
                else:
                    choices[player] = return_dict['choice']

            except Exception as e:
                choices[player] = "crash"
                lerror = str(e)

            if choices[player] == "crash":
                print(player+" ("+names[player]+") has crashed :( :"+lerror)
                history[player].append("crash")
                crashes[player]+=1
                c.execute("INSERT INTO actions (key, value) VALUES (?, ?)", [player, choices[player]])
                c.execute(
                    "UPDATE statistics SET crashes = " + str(crashes[player]) + " WHERE key = ?",
                    [player])
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
                    c.execute("UPDATE game SET y = " + str(coords[player]["y"]) + " WHERE key = ?", [player])
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
                    c.execute("UPDATE game SET y = " + str(coords[player]["y"]) + " WHERE key = ?", [player])
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
                    c.execute("UPDATE game SET x = " + str(coords[player]["x"]) + " WHERE key = ?", [player])
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
                    c.execute("UPDATE game SET x = " + str(coords[player]["x"]) + " WHERE key = ?", [player])
                    c.execute(
                        "DELETE FROM coins WHERE x = ? AND y = ?",
                        [coords[player]["x"], coords[player]["y"]])
            if choices[player]=="go_up" or choices[player] == "go_down" or choices[player] == "go_left" or choices[player] == "go_right" or  choices[player] == "fire_up" or choices[player] == "fire_down" or choices[player] == "fire_left" or choices[player] == "fire_right" or choices[player] == "crash" or choices[player] == "self_destruct" or choices[player] == "shield":
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
                        break;
                    if mainMap[px][y] not in ('.', '@'):
                        hit_player = mainMap[px][y]

                        actual = apply_damage(hit_player, 1, health, shield, choices, healthMap, px, y)

                        if actual > 0:
                            kills[player]+=1

                        '''
                        print(player + " (" + str(health[player]) + ") hits " + str(hit_player) + " (" + str(
                            health[hit_player]) + ")" + " [" + str(px) + " ," + str(py) + "] -> [" + str(px) + ", " + str(
                            y) + "] " + choices[player])
                            '''



                        c.execute("UPDATE game SET life = " + str(health[hit_player]) + ", shield = " + str(shield[hit_player]) + " WHERE key = ?", [hit_player])
                        break
            if choices[player] == "fire_down":
                shots[player] += 1
                for y in range(py+1, int(settings["height"])):
                    if mainMap[px][y] == '#':
                        break
                    if mainMap[px][y] not in ('.', '@'):
                        hit_player = mainMap[px][y]

                        actual = apply_damage(hit_player, 1, health, shield, choices, healthMap, px, y)

                        if actual > 0:
                            kills[player] += 1

                        print(player + " ("+str(health[player])+") hits " + str(hit_player) + " (" + str(
                            health[hit_player]) + ")" + " [" + str(px) + " ," + str(py) + "] -> ["+str(px)+", "+str(y)+"] " + choices[player])



                        c.execute("UPDATE game SET life = " + str(health[hit_player]) + ", shield = " + str(shield[hit_player]) + " WHERE key = ?", [hit_player])
                        break
            if choices[player] == "fire_left":
                shots[player] += 1
                for x in range(px-1, -1, -1):
                    if mainMap[x][py] == '#':
                        break
                    if mainMap[x][py] not in ('.', '@'):
                        hit_player = mainMap[x][py]

                        actual = apply_damage(hit_player, 1, health, shield, choices, healthMap, x, py)

                        if actual > 0:
                            kills[player] += 1

                        print(player + " (" + str(health[player]) + ") hits " + str(hit_player) + " (" + str(
                            health[hit_player]) + ")" + " [" + str(px) + " ," + str(py) + "] -> [" + str(x) + ", " + str(
                            py) + "] " + choices[player])



                        c.execute("UPDATE game SET life = " + str(health[hit_player]) + ", shield = " + str(shield[hit_player]) + " WHERE key = ?", [hit_player])
                        break
            if choices[player] == "fire_right":
                shots[player] += 1
                for x in range(px+1, int(settings["width"])):
                    if mainMap[x][py] == '#':
                        break
                    if mainMap[x][py] not in ('.', '@'):
                        hit_player = mainMap[x][py]

                        actual = apply_damage(hit_player, 1, health, shield, choices, healthMap, x, py)

                        if actual > 0:
                            kills[player] += 1

                        print(player + " (" + str(health[player]) + ") hits " + str(hit_player) + " (" + str(
                            health[hit_player]) + ")" + " [" + str(px) + " ," + str(py) + "] -> [" + str(x) + ", " + str(
                            py) + "] " + choices[player])




                        c.execute("UPDATE game SET life = " + str(health[hit_player]) + ", shield = " + str(shield[hit_player]) + " WHERE key = ?", [hit_player])
                        break

            if choices[player] == "self_destruct":
                print(player + " self-destructs!")
                
                for dx in range(-3, 4):
                    for dy in range(-3, 4):
                        if dx == 0 and dy == 0:
                            continue
                        tx, ty = px + dx, py + dy
                        if not (0 <= tx < int(settings["width"]) and 0 <= ty < int(settings["height"])):
                            continue
                        # Проверка линии видимости (Брезенхэм)
                        blocked = False
                        sx, sy = abs(dx), abs(dy)
                        n = max(sx, sy)
                        for step in range(1, n):
                            cx = px + round(dx * step / n)
                            cy = py + round(dy * step / n)
                            if mainMap[cx][cy] == '#':
                                blocked = True
                                break
                        
                        if not blocked and mainMap[tx][ty] not in ('.', '@', '#'):
                            hit_player = mainMap[tx][ty]
                            actual = apply_damage(hit_player, 3, health, shield, choices, healthMap, tx, ty)
                            if actual > 0:
                                kills[player] += 1
                            c.execute("UPDATE game SET life = " + str(health[hit_player]) + ", shield = " + str(shield[hit_player]) + " WHERE key = ?", [hit_player])
                
                c.execute("UPDATE statistics SET kills = " + str(kills[player]) + " WHERE key = ?", [player])
                c.execute("UPDATE statistics SET lifetime = " + str(ticks) + " WHERE key = ?", [player])
                c.execute("UPDATE statistics SET shots = " + str(shots[player]) + " WHERE key = ?", [player])
                c.execute("UPDATE statistics SET coins = " + str(coins[player]) + " WHERE key = ?", [player])
                c.execute("UPDATE statistics SET steps = " + str(steps[player]) + " WHERE key = ?", [player])
                c.execute("UPDATE statistics SET errors = " + str(errors[player]) + " WHERE key = ?", [player])

                health[player] = 0
                healthMap[px][py] = 0
                mainMap[px][py] = '.'
                c.execute("UPDATE game SET life = 0 WHERE key = ?", [player])

            if choices[player] == "fire_up" or choices[player] == "fire_down" or choices[player] == "fire_left" or choices[player] == "fire_right":
                c.execute(
                    "UPDATE statistics SET kills = " + str(kills[player]) + " WHERE key = ?",
                    [player])
                #print(player + " sent "+choices[player])

                # db record

            if int(health[player])>0:
                c.execute(
                    "UPDATE statistics SET lifetime = " + str(ticks) + " WHERE key = ?",
                    [player])
                c.execute(
                    "UPDATE statistics SET shots = " + str(shots[player]) + " WHERE key = ?",
                    [player])
                c.execute(
                    "UPDATE statistics SET coins = " + str(coins[player]) + " WHERE key = ?",
                    [player])
                c.execute(
                    "UPDATE statistics SET steps = " + str(steps[player]) + " WHERE key = ?",
                    [player])
                c.execute(
                    "UPDATE statistics SET errors = " + str(errors[player]) + " WHERE key = ?",
                    [player])


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
    return settings

while 1:
    s = make_testing()
    if s['mode']!='sandbox':
        time.sleep(60)
        break
    time.sleep(3)










