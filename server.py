__author__ = 'roctbb'
import tornado.web
import tornado.httpserver
import sqlite3
import sys
import os
import json
import random
import string

os.chdir(os.path.dirname(os.path.realpath(__file__)))

from time import gmtime, strftime
def getKey(N):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(N))

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("upload.html")
    def post(self):
        try:
            file = self.request.files['file'][0]
            conn = sqlite3.connect('tanks.sqlite')
            c = conn.cursor()
            c.execute("SELECT * FROM players WHERE key = '%s'"%self.get_argument("key"))
            player = c.fetchone()
            c.execute("SELECT * FROM settings")
            result = c.fetchall()
            settings = dict()
            for string in result:
                settings[string[1]] = string[2]
            if settings["mode"] == "sandbox":
                if player[3]=="waiting":
                    print(strftime("%Y-%m-%d %H:%M:%S", gmtime())+": "+player[2]+" ("+player[1]+") has loaded new bot")
                else:
                    print(strftime("%Y-%m-%d %H:%M:%S", gmtime())+": "+player[2] + " (" + player[1] + ") has reloaded bot")
                c.execute("UPDATE players SET code = ? WHERE key = ?", [file['body'], player[2]])
                c.execute("UPDATE players SET state = ? WHERE key = ?", ["ready", player[2]])
                conn.commit()
            else:
                if player[3]=="waiting" or settings['game_state']!="running":
                    c.execute("UPDATE players SET state = ?", ["ready"])
                    c.execute("UPDATE players SET code = ?", [file['body']])
                    conn.commit()
                else:
                    self.write("<script>alert('Игра уже запущена!');location.href=location.href;</script>")
                    return

            self.redirect("/game")
        except Exception as e:
            print(e)
            self.write("<script>alert('Ошибка загрузки!');location.href=location.href;</script>")

        sys.path.append(os.path.dirname(__file__) + "/bots")

class RegisterHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("register.html")
    def post(self):
        name = self.get_argument('key', None)
        if name is None:
            self.redirect('/register')
        else:
            conn = sqlite3.connect('tanks.sqlite')
            c = conn.cursor()
            key = getKey(8)
            c.execute("INSERT INTO players (name, key, state, code) VALUES (?,?,?,?)", [name, key, "waiting", None])
            conn.commit()
            self.write("<string>Ваш ключ: </strong> {}".format(key))


class StatsHandler(tornado.web.RequestHandler):
    def get(self):
        conn = sqlite3.connect('tanks.sqlite')
        gamestate=[]
        c = conn.cursor()
        c.execute("SELECT * FROM players")
        result = c.fetchall()
        names = dict()
        for record in result:
            names[record[2]] = record[1]
        c.execute("SELECT * FROM statistics")
        result = c.fetchall()
        for record in result:
            name = names[record[1]]
            kills = record[2]
            lifetime = record[3]
            shots = record[5]
            steps = record[4]
            crashes = record[6]
            errors = record[7]
            lastCrash = record[8]
            coins = record[9]
            quality = "good"
            quality_class = "label-success"
            if (crashes>0):
                quality_class = "label-danger"
                quality = "crash"
            elif (errors>0):
                quality = "errors"
                quality_class = "label-warning"
            points = coins*50 + kills*20+lifetime-crashes*5
            life = 0
            c.execute("SELECT life FROM game WHERE key = ?", [record[1]])
            l = c.fetchall()
            if len(l)>0 :
                life = l[0][0]
            gamestate.append({"name": name,"hp":life, "kills": kills, "lifetime": lifetime, "score": points, "shots": shots,
                              "steps": steps, "quality": quality, "quality_class": quality_class, "lastCrash": lastCrash, "coins": coins})

        self.render("stats.html", gamestate = sorted(gamestate, key=lambda k: -k['score']))
class GameHandler(tornado.web.RequestHandler):
    def get(self):
        conn = sqlite3.connect('tanks.sqlite')
        c = conn.cursor()
        c.execute("SELECT * FROM settings")
        result = c.fetchall()
        settings = dict()
        for string in result:
            settings[string[1]] = string[2]
        with open('map.txt') as map_file:
            map_data = map_file.read()
            mainMap = map_data.split('\n')
            for i in range(len(mainMap)):
                mainMap[i] = mainMap[i].split(' ')
            settings["height"] = len(mainMap[0])
            settings["width"] = len(mainMap)
        self.render("game.html", width=settings["width"], height=settings["height"])

class StateHandler(tornado.web.RequestHandler):
    def get(self):
        conn = sqlite3.connect('tanks.sqlite')
        c = conn.cursor()
        c.execute("SELECT * FROM settings")
        result = c.fetchall()
        settings = dict()
        for string in result:
            settings[string[1]] = string[2]
        with open('map.txt') as map_file:
            map_data = map_file.read()
            mainMap = map_data.split('\n')
            for i in range(len(mainMap)):
                mainMap[i] = mainMap[i].split(' ')
            settings["height"] = len(mainMap[0])
            settings["width"] = len(mainMap)

        c.execute("SELECT * FROM players")
        result = c.fetchall()
        names=dict()
        for record in result:
            names[record[2]]=record[1]


        c.execute("SELECT * FROM game")
        result = c.fetchall()
        for record in result:
            x = record[2]
            y = record[3]
            life = record[4]
            name = names[record[1]]
            mainMap[x][y] = {'name': name, 'life': life, 'hit': 0}
        for record in result:
            x = record[2]
            y = record[3]
            c.execute("SELECT value FROM actions WHERE key = ? ORDER BY id DESC LIMIT 1", [record[1]])
            action = c.fetchall()
            if len(action)<1:
                continue
            action=action[0]
            if action[0] == "fire_up":
                for i in range(y - 1, -1, -1):
                    if mainMap[x][i] != '.' and mainMap[x][i] != '&uarr;' and mainMap[x][i] != '&darr;' and mainMap[x][i] != '&larr;' and mainMap[x][i] != '&rarr;' and mainMap[x][i] != '#' and mainMap[x][i] != '@':
                        mainMap[x][i]['hit']=1
                        break
                    elif mainMap[x][i] == '#' or mainMap[x][i] == '@':
                        break
                    else:
                        mainMap[x][i] = '&uarr;'
            if action[0] == "fire_down":
                for i in range(y + 1, int(settings['height'])):
                    if mainMap[x][i] != '.' and mainMap[x][i] != '&uarr;' and mainMap[x][i] != '&darr;' and mainMap[x][i] != '&larr;' and mainMap[x][i] != '&rarr;' and mainMap[x][i] != '#' and mainMap[x][i] != '@':
                        mainMap[x][i]['hit'] = 1
                        break
                    elif mainMap[x][i] == '#' or mainMap[x][i] == '@':
                        break
                    else:
                        mainMap[x][i] = '&darr;'
            if action[0] == "fire_left":
                for i in range(x - 1, -1, -1):
                    if mainMap[i][y] != '.' and mainMap[i][y] != '&uarr;' and mainMap[i][y] != '&darr;' and mainMap[i][y] != '&larr;' and mainMap[i][y] != '&rarr;' and mainMap[i][y] != '#' and mainMap[i][y] != '@':
                        mainMap[i][y]['hit'] = 1
                        break
                    elif mainMap[i][y] == '#' or mainMap[i][y] == '@':
                        break
                    else:
                        mainMap[i][y] = '&larr;'
            if action[0] == "fire_right":
                for i in range(x + 1, int(settings['width'])):
                    if mainMap[i][y] != '.' and mainMap[i][y] != '&uarr;' and mainMap[i][y] != '&darr;' and mainMap[i][y] != '&larr;' and mainMap[i][y] != '&rarr;' and mainMap[i][y] != '#' and mainMap[i][y] != '@':
                        mainMap[i][y]['hit'] = 1
                        break
                    elif mainMap[i][y] == '#' or mainMap[i][y] == '@':
                        break
                    else:
                        mainMap[i][y] = '&rarr;'
        for record in result:
            if record[4]<=0:
                c.execute("DELETE FROM game WHERE id = ?", [record[0]])
        c.execute("SELECT * FROM coins")
        result = c.fetchall()
        for record in result:
            x = record[0]
            y = record[1]
            mainMap[x][y]='@'
        conn.commit()
        self.write(json.dumps(mainMap))

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/", MainHandler),(r"/register", RegisterHandler),(r"/game", GameHandler),(r"/state", StateHandler), (r"/stats", StatsHandler),(r'/static/(.*)', tornado.web.StaticFileHandler, {'path': os.path.dirname(__file__)+"/static/"}),]
        settings = {}
        super(Application, self).__init__(handlers, **settings)

def main():
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(8085)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()