import random


def security_check(x, y, field):
    width = len(field)
    height = len(field[0])
    if x < 0:
        return False
    if y < 0:
        return False
    if x > width - 1:
        return False
    if y > height - 1:
        return False


def last_action(x, y, field):
    if field[x][y]['history'] == []:
        return ''
    return field[x][y]['history'][-1]


def check_money(x, y, field):
    print("checking money")

    width = len(field)
    height = len(field[0])

    money_right = 1000
    money_left = 1000
    money_top = 1000
    money_bottom = 1000

    for i in range(x - 1, -1, -1):
        if field[i][y] == -1:
            break
        if field[i][y] == 1:
            money_left = abs(x - i)

    for i in range(x + 1, width):
        if field[i][y] == -1:
            break
        if field[i][y] == 1:
            money_right = abs(x - i)

    for i in range(y + 1, height):
        if field[x][i] == -1:
            break
        if field[x][i] == 1:
            money_bottom = abs(y - i)

    for i in range(y - 1, -1, -1):
        if field[x][i] == -1:
            break
        if field[x][i] == 1:
            money_top = abs(y - i)

    if money_top == min([money_top, money_bottom, money_left, money_right, 999]):
        print("heading up for money")
        return "go_up"
    if money_bottom == min([money_top, money_bottom, money_left, money_right, 999]):
        print("heading down for money")
        return "go_down"
    if money_left == min([money_top, money_bottom, money_left, money_right, 999]):
        print("heading left for money")
        return "go_left"
    if money_right == min([money_top, money_bottom, money_left, money_right, 999]):
        print("heading right for money")
        return "go_right"
    print("no money - no honey :(")
    return False


def check_battle(x, y, field):
    print("checking enemies")

    life = field[x][y]['life']

    width = len(field)
    height = len(field[0])

    enemy_left = False
    enemy_right = False
    enemy_top = False
    enemy_bottom = False

    crush_left = False
    crush_right = False
    crush_top = False
    crush_bottom = False

    print([enemy_left, enemy_right, enemy_bottom, enemy_top])

    for i in range(x - 1, -1, -1):
        if field[i][y] == -1:
            break
        if field[i][y] not in [0, 1]:
            enemy_left = field[i][y]['life']
            if field[i][y]['history'] != [] and field[i][y]['history'][-1] in ['error', 'crash']:
                crush_left = True

    for i in range(x + 1, width):
        if field[i][y] == -1:
            break
        if field[i][y] not in [0, 1]:
            enemy_right = field[i][y]['life']
            if field[i][y]['history'] != [] and field[i][y]['history'][-1] in ['error', 'crash']:
                crush_right = True

    for i in range(y + 1, height):
        if field[x][i] == -1:
            break
        if field[x][i] not in [0, 1]:
            enemy_bottom = field[x][i]['life']
            if field[x][i]['history'] != [] and field[x][i]['history'][-1] in ['error', 'crash']:
                crush_bottom = True

    for i in range(y - 1, -1, -1):
        if field[x][i] == -1:
            break
        if field[x][i] not in [0, 1]:
            enemy_top = field[x][i]['life']
            if field[x][i]['history'] != [] and field[x][i]['history'][-1] in ['error', 'crash']:
                crush_top = True
    if crush_left:
        enemy_left = 1
    if crush_right:
        enemy_right = 1
    if crush_bottom:
        enemy_bottom = 1
    if crush_top:
        enemy_top = 1
    print([enemy_left, enemy_right, enemy_bottom, enemy_top])

    sumlifes = int(enemy_bottom) + int(enemy_top) + int(enemy_right) + int(enemy_left) \
               - int(crush_top) - int(crush_bottom) - int(crush_left) - int(crush_right)

    if sumlifes >= field[x][y]['life'] and sumlifes != 0:
        print("I'm in trouble")
        if not enemy_top and not enemy_bottom:
            print("vertical clear")
            if last_action(x, y, field) == "go_up" and y > 0 and field[x][y - 1] != -1:
                print("heading up - history is hear")
                return "go_up"
            if y < height - 1 and field[x][y + 1] != -1:
                print("heading down")
                return "go_down"
            if y > 0 and field[x][y - 1] != -1:
                print("heading up")
                return "go_up"
            print("no chances((")
            return random.choice(["go_left", "go_right"])
        if not enemy_left and not enemy_right:
            print("horizontal clear")
            if last_action(x, y, field) == "go_right" and x < width - 1 and field[x + 1][y] != -1:
                print("heading right - history is hear")
                return "go_right"
            if x > 0 and field[x - 1][y] != -1:
                print("heading left")
                return "go_left"
            if x < width - 1 and field[x + 1][y] != -1:
                print("heading right")
                return "go_right"
            print("no chances((")
            return random.choice(["go_up", "go_down"])
        print("too hard - just random running away")
        return random.choice(["go_up", "go_down", "go_left", "go_right"])

    if enemy_left and not crush_left:
        print("save fire left")
        return "fire_left"
    if enemy_top and not crush_top:
        print("save fire up")
        return "fire_up"
    if enemy_bottom and not crush_bottom:
        print("save fire down")
        return "fire_down"
    if enemy_right and not crush_right:
        print("save fire right")
        return "fire_right"
    if enemy_left:
        print("save fire left")
        return "fire_left"
    if enemy_top:
        print("save fire up")
        return "fire_up"
    if enemy_bottom:
        print("save fire down")
        return "fire_down"
    if enemy_right:
        print("save fire right")
        return "fire_right"
    print("nothing found - life's good")
    return False


def make_choice(x, y, field):
    width = len(field)
    height = len(field[0])

    result = check_battle(x, y, field)
    print(result)
    if result != False:
        return result

    result = check_money(x, y, field)
    print(result)
    if result != False:
        return result

    while True:
        variants = []
        if y > 0 and field[x][y - 1] != -1:
            variants.append("go_up")
        if y < height - 1 and field[x][y + 1] != -1:
            variants.append("go_down")
        if x > 0 and field[x - 1][y] != -1:
            variants.append("go_left")
        if x < width - 1 and field[x + 1][y] != -1:
            variants.append("go_right")
        if field[x][y]['history'] != [] and field[x][y]['history'][-1] in variants:
            return field[x][y]['history'][-1]
        return random.choice(variants)
