import random

import pygame


class Obstacle(pygame.sprite.Sprite):
    def __init__(self, pos, size, kind="tombstone"):
        super().__init__()
        self.kind = kind
        self.image = pygame.Surface(size, pygame.SRCALPHA)
        if kind == "tree":
            pygame.draw.rect(self.image, (76, 50, 38), (size[0] // 2 - 5, size[1] // 3, 10, size[1] // 2))
            pygame.draw.circle(self.image, (45, 62, 54), (size[0] // 2, size[1] // 3), size[0] // 3)
        elif kind == "wall":
            pygame.draw.rect(self.image, (79, 78, 88), (0, size[1] // 3, size[0], size[1] // 2), border_radius=5)
            for x in range(0, size[0], 18):
                pygame.draw.line(self.image, (48, 47, 56), (x, size[1] // 3), (x, size[1] - 4), 1)
        else:
            pygame.draw.rect(self.image, (92, 92, 105), (8, 8, size[0] - 16, size[1] - 8), border_radius=6)
            pygame.draw.rect(self.image, (55, 55, 68), (12, 16, size[0] - 24, 4))
        self.rect = self.image.get_rect(center=pos)
        self.collision_rect = self.make_collision_rect(size, kind)
        self.collision_rect.center = self.rect.center

    @staticmethod
    def make_collision_rect(size, kind):
        """返回比整张贴图更贴近可见部分的碰撞框。"""
        width, height = size
        if kind == "tree":
            # 树的透明边缘和树冠外围不应阻挡角色，树干附近保留较小判定区。
            rect = pygame.Rect(0, 0, max(18, int(width * 0.46)), max(18, int(height * 0.38)))
            rect.midbottom = (width // 2, int(height * 0.86))
            return rect
        if kind == "wall":
            # 墙体实际绘制在图片中部，去掉上下透明区域和少量左右留白。
            return pygame.Rect(
                int(width * 0.06),
                int(height * 0.33),
                max(24, int(width * 0.88)),
                max(16, int(height * 0.48)),
            )

        # 墓碑保留主体区域，忽略贴图四周的透明边缘。
        return pygame.Rect(
            int(width * 0.16),
            int(height * 0.12),
            max(18, int(width * 0.68)),
            max(22, int(height * 0.76)),
        )


def make_obstacles():
    random.seed(11)
    obstacles = pygame.sprite.Group()
    kinds = ["tombstone", "tree", "wall"]
    for _ in range(45):
        x = random.randint(-1800, 1800)
        y = random.randint(-1400, 1400)
        if abs(x) < 180 and abs(y) < 160:
            continue
        kind = random.choice(kinds)
        size = (random.randint(42, 76), random.randint(42, 82))
        if kind == "wall":
            size = (random.randint(90, 150), random.randint(38, 56))
        obstacles.add(Obstacle((x, y), size, kind))
    return obstacles
