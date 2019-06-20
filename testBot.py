import random


class RandomBot:
    actions = ['go_left', 'go_right', 'go_up', 'go_down',
               'fire_left', 'fire_right', 'fire_up', 'fire_down']

    def make_choice(self, x, y, field):
        return random.choice(self.actions)


class MoveBot:
    def make_choice(self, x, y, field):
        possible_actions = self.get_possible_actions(x, y, field)
        return random.choice(possible_actions)

    def get_possible_actions(self, x, y, field):

        res = []
        lenx = len(field[0])
        leny = len(field)

        if x + 1 < lenx and field[y][x+1] == '0':
            res.append('go_right')
        if x - 1 >= 0 and field[y][x-1] == '0':
            res.append('go_left')
        if y - 1 >= 0 and field[y-1][x] == '0':
            res.append('go_up')
        if y + 1 < leny and field[y+1][x] == '0':
            res.append('go_down')

        return res


def make_choice(x, y, field):
    return RandomBot().make_choice(x, y, field)


if __name__ == "__main__":
    field = [
        ['0', '9', '9', '9'],
        ['0', '9', '9', '9'],
        ['0', '9', '9', '9'],
        ['0', '0', '0', '0']
    ]
    print(make_choice(3, 1, field))