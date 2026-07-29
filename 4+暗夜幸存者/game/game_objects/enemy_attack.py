import math

import pygame

from utils.math_utils import is_line_blocked, safe_normalize


class EnemyAttack(pygame.sprite.Sprite):
    """敌人技能的预警和伤害区域。

    目前支持圆形和直线两种形状，足够表现冲撞、激光、震地、爆炸和腐蚀区。
    """

    def __init__(
        self, pos, shape, damage, warn_time, active_time,
        radius=80, length=300, width=36, angle=0,
        color=(220, 58, 78), stun=0, repeat=False, hit_interval=0.7,
        source_pos=None, blocked_by_obstacles=False
    ):
        super().__init__()
        self.pos = pygame.Vector2(pos)
        self.shape = shape
        self.damage = int(damage)
        self.warn_time = warn_time
        self.active_time = active_time
        self.radius = radius
        self.length = length
        self.width = width
        self.angle = angle
        self.color = color
        self.stun = stun
        self.repeat = repeat
        self.hit_interval = hit_interval
        self.source_pos = pygame.Vector2(source_pos) if source_pos is not None else None
        self.blocked_by_obstacles = blocked_by_obstacles
        self.hit_timer = 0
        self.has_hit = False
        self.active = False
        self.image = self.make_image()
        self.rect = self.image.get_rect(center=self.pos)

    def make_image(self):
        alpha = 185 if self.active else 92
        line_width = 0 if self.active else 3
        color = (*self.color[:3], alpha)
        if self.shape == "line":
            surface = pygame.Surface((self.length, self.width), pygame.SRCALPHA)
            rect = surface.get_rect()
            pygame.draw.rect(surface, color, rect, border_radius=self.width // 2)
            if not self.active:
                pygame.draw.rect(surface, (*self.color[:3], 190), rect, 3, border_radius=self.width // 2)
            return pygame.transform.rotate(surface, -math.degrees(self.angle))

        size = self.radius * 2 + 8
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        pygame.draw.circle(surface, color, center, self.radius, line_width)
        if not self.active:
            pygame.draw.circle(surface, (*self.color[:3], 195), center, self.radius, 3)
        return surface

    def update(self, dt, obstacles=None):
        if self.blocked_by_obstacles and self.source_pos is not None:
            if is_line_blocked(self.source_pos, self.pos, obstacles):
                self.kill()
                return
        if self.hit_timer > 0:
            self.hit_timer = max(0, self.hit_timer - dt)
        if not self.active:
            self.warn_time -= dt
            if self.warn_time <= 0:
                self.active = True
                self.image = self.make_image()
                self.rect = self.image.get_rect(center=self.pos)
            return

        self.active_time -= dt
        if self.active_time <= 0:
            self.kill()

    def can_hit(self):
        if not self.active:
            return False
        if self.repeat:
            return self.hit_timer <= 0
        return not self.has_hit

    def mark_hit(self):
        self.has_hit = True
        self.hit_timer = self.hit_interval

    def collides_player(self, player):
        player_pos = pygame.Vector2(player.collision_rect.center)
        player_radius = player.collision_radius
        if self.shape == "line":
            direction = pygame.Vector2(math.cos(self.angle), math.sin(self.angle))
            start = self.pos - direction * (self.length / 2)
            end = self.pos + direction * (self.length / 2)
            segment = end - start
            if segment.length_squared() == 0:
                return False
            t = max(0, min(1, (player_pos - start).dot(segment) / segment.length_squared()))
            closest = start + segment * t
            return closest.distance_to(player_pos) <= self.width / 2 + player_radius
        return self.pos.distance_to(player_pos) <= self.radius + player_radius


def line_attack_between(start_pos, target_pos, damage, warn_time, active_time, width, stun=0, color=(220, 58, 78)):
    start = pygame.Vector2(start_pos)
    target = pygame.Vector2(target_pos)
    direction = safe_normalize(target - start)
    if direction.length_squared() == 0:
        direction = pygame.Vector2(1, 0)
    length = min(760, max(180, start.distance_to(target) + 140))
    center = start + direction * (length / 2)
    angle = math.atan2(direction.y, direction.x)
    return EnemyAttack(center, "line", damage, warn_time, active_time, length=round(length), width=width, angle=angle, stun=stun, color=color)
