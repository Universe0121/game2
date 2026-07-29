import pygame


class DropItem(pygame.sprite.Sprite):
    def __init__(self, kind, pos, value):
        super().__init__()
        self.kind = kind
        self.value = value
        self.pos = pygame.Vector2(pos)
        self.image = self.make_image()
        self.rect = self.image.get_rect(center=self.pos)

    def make_image(self):
        surface = pygame.Surface((22, 22), pygame.SRCALPHA)
        if self.kind == "exp":
            pygame.draw.polygon(surface, (76, 210, 230), [(11, 1), (20, 9), (16, 21), (6, 21), (2, 9)])
            pygame.draw.polygon(surface, (190, 246, 255), [(11, 4), (17, 10), (11, 18), (5, 10)], 1)
        elif self.kind == "chest":
            pygame.draw.rect(surface, (132, 75, 32), (3, 8, 16, 11), border_radius=2)
            pygame.draw.rect(surface, (214, 174, 72), (3, 6, 16, 5), border_radius=2)
            pygame.draw.rect(surface, (245, 224, 122), (10, 8, 3, 9))
        elif self.kind == "spinach_can":
            pygame.draw.rect(surface, (53, 118, 70), (4, 3, 14, 17), border_radius=3)
            pygame.draw.rect(surface, (214, 230, 190), (6, 7, 10, 5))
            pygame.draw.arc(surface, (28, 72, 42), (7, 9, 9, 8), 0.4, 4.2, 2)
        else:
            pygame.draw.circle(surface, (226, 64, 82), (11, 11), 9)
            pygame.draw.circle(surface, (255, 220, 220), (8, 8), 3)
        return surface

    def move_towards(self, target_pos, dt):
        direction = target_pos - self.pos
        if direction.length_squared() > 0:
            self.pos += direction.normalize() * 420 * dt
            self.rect.center = (round(self.pos.x), round(self.pos.y))
