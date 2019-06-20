from copy import deepcopy

def make_choice(startX, startY, mapOfCoins):

    width = len(mapOfCoins)
    height = len(mapOfCoins[0])

    visitedMap = deepcopy(mapOfCoins)
    path = []

    points = [(startX, startY, 0, path)]

    while len(points) != 0:
        # ищем самую близкую точку из доступных
        points = sorted(points, key=lambda x: x[2])
        x, y, S, path = points[0]
        del points[0]

        # если точка за пределами поля
        if x < 0 or y < 0 or x >= width or y >= height:
            continue

        # если мы уже были в точке
        if visitedMap[x][y] == -1:
            continue

        if visitedMap[x][y] not in [-1,0,1] and (x,y)!=(startX, startY):
            continue

        # если нашли монетку
        if mapOfCoins[x][y] == 1:
            return path[0]

        visitedMap[x][y] = -1
        # добавляем соседей в очередь
        newPath = deepcopy(path)
        newPath.append('go_right')
        points.append((x+1, y, S+1, newPath))

        newPath = deepcopy(path)
        newPath.append('go_down')
        points.append((x, y+1, S+1, newPath))

        newPath = deepcopy(path)
        newPath.append('go_left')
        points.append((x-1, y, S+1, newPath))

        newPath = deepcopy(path)
        newPath.append('go_up')
        points.append((x, y-1, S+1, newPath))

    return "fire_up"