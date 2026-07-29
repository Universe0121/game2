import math
import random

import pygame


def safe_normalize(vector):
    if vector.length_squared() == 0:
        return pygame.Vector2()
    return vector.normalize()


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def random_spawn_position(center, width, height, padding):
    """在屏幕外侧随机生成一个世界坐标。"""
    side = random.choice(("top", "bottom", "left", "right"))
    x = random.uniform(center.x - width / 2 - padding, center.x + width / 2 + padding)
    y = random.uniform(center.y - height / 2 - padding, center.y + height / 2 + padding)
    if side == "top":
        y = center.y - height / 2 - padding
    elif side == "bottom":
        y = center.y + height / 2 + padding
    elif side == "left":
        x = center.x - width / 2 - padding
    else:
        x = center.x + width / 2 + padding
    return pygame.Vector2(x, y)


def is_line_blocked(start_pos, end_pos, obstacles):
    """判断两点之间是否被障碍物挡住。"""
    if obstacles is None:
        return False

    start = pygame.Vector2(start_pos)
    end = pygame.Vector2(end_pos)
    line = ((round(start.x), round(start.y)), (round(end.x), round(end.y)))
    for obstacle in obstacles:
        rect = getattr(obstacle, "collision_rect", obstacle.rect)
        if rect.clipline(line):
            return True
    return False
