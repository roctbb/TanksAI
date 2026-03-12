import random


def make_choice(x, y, field):
    """
    Пример бота с самоуничтожением.
    Самоуничтожается, если рядом есть враги.
    """
    # Проверяем, есть ли враги в радиусе 3 клеток
    enemies_nearby = 0
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            tx, ty = x + dx, y + dy
            if 0 <= tx < len(field) and 0 <= ty < len(field[0]):
                cell = field[tx][ty]
                if isinstance(cell, dict) and 'name' in cell:
                    enemies_nearby += 1

    # Если рядом 2+ врагов, самоуничтожаемся
    if enemies_nearby >= 2:
        return "self_destruct"

    # Иначе обычная логика
    return random.choice(['go_left', 'go_right', 'go_up', 'go_down'])
