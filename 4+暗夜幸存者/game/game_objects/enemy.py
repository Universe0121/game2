import random

import pygame

from utils.math_utils import is_line_blocked, safe_normalize


class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_id, data, pos, image=None, hp_scale=1.0, speed_scale=1.0):
        super().__init__()
        self.enemy_id = enemy_id
        self.data = data
        self.name = data["name"]
        self.max_hp = int(data["hp"] * hp_scale)
        self.hp = self.max_hp
        self.speed = data["speed"] * speed_scale
        self.damage = data["damage"]
        self.exp = data["exp"]
        self.coin = data["coin"]
        self.is_boss = data.get("boss", False)
        self.is_elite = data.get("elite", False)
        self.is_ranged = data.get("ranged", False)
        self.shoot_timer = data.get("shoot_cooldown", 2.0)
        self.skill_timer = random.uniform(1.0, data.get("skill_cooldown", 5.0))
        self.charge_delay = 0
        self.charge_timer = 0
        self.charge_velocity = pygame.Vector2()
        self.teleport_delay = 0
        self.teleport_target = None
        self.radius = data["radius"]
        self.pos = pygame.Vector2(pos)
        self.hit_flash_timer = 0

        self.image = image if image else self.make_fallback_image(tuple(data["color"]))
        self.rect = self.image.get_rect(center=self.pos)

    def make_fallback_image(self, color):
        size = self.radius * 2 + 8
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(surface, color, (size // 2, size // 2), self.radius)
        pygame.draw.circle(surface, (18, 15, 24), (size // 2 - 5, size // 2 - 3), 3)
        pygame.draw.circle(surface, (18, 15, 24), (size // 2 + 5, size // 2 - 3), 3)
        if self.is_boss:
            pygame.draw.circle(surface, (235, 197, 83), (size // 2, size // 2), self.radius + 2, 3)
        elif self.is_elite:
            pygame.draw.circle(surface, (230, 210, 120), (size // 2, size // 2), self.radius + 1, 2)
        return surface

    def update(self, dt, player_pos, obstacles):
        self.update_action_timers(dt)
        if self.charge_delay > 0 or self.teleport_delay > 0:
            return

        direction = safe_normalize(player_pos - self.pos)
        if self.charge_timer > 0:
            move = self.charge_velocity * dt
        else:
            move = direction * self.speed * dt
        # 分轴移动：撞到障碍物时保留另一个方向的移动，减少墙角抖动和卡死。
        self.pos.x += move.x
        self.rect.centerx = round(self.pos.x)
        if any(self.rect.colliderect(obstacle.collision_rect) for obstacle in obstacles):
            self.pos.x -= move.x
            self.rect.centerx = round(self.pos.x)

        self.pos.y += move.y
        self.rect.centery = round(self.pos.y)
        if any(self.rect.colliderect(obstacle.collision_rect) for obstacle in obstacles):
            self.pos.y -= move.y
            self.rect.centery = round(self.pos.y)

    def update_action_timers(self, dt):
        if self.hit_flash_timer > 0:
            self.hit_flash_timer = max(0, self.hit_flash_timer - dt)
        if self.charge_delay > 0:
            self.charge_delay = max(0, self.charge_delay - dt)
            return
        if self.charge_timer > 0:
            self.charge_timer = max(0, self.charge_timer - dt)
        if self.teleport_delay > 0:
            self.teleport_delay = max(0, self.teleport_delay - dt)
            if self.teleport_delay == 0 and self.teleport_target is not None:
                self.pos = pygame.Vector2(self.teleport_target)
                self.rect.center = (round(self.pos.x), round(self.pos.y))
                self.teleport_target = None

    def start_charge(self, direction, delay=0.72, duration=0.34, speed=560):
        self.charge_delay = delay
        self.charge_timer = duration
        self.charge_velocity = safe_normalize(direction) * speed

    def start_teleport(self, target_pos, delay=0.62):
        self.teleport_delay = delay
        self.teleport_target = pygame.Vector2(target_pos)

    def take_damage(self, amount):
        self.hp -= amount
        self.hit_flash_timer = 0.09
        return self.hp <= 0

    def can_shoot(self, dt, player_pos):
        if not self.is_ranged:
            return False
        self.shoot_timer -= dt
        if self.shoot_timer > 0:
            return False
        if self.pos.distance_to(player_pos) > self.data.get("shoot_range", 600):
            return False
        self.shoot_timer = self.data.get("shoot_cooldown", 2.0)
        return True


class EnemyProjectile(pygame.sprite.Sprite):
    def __init__(
        self, pos, target_pos, damage, speed, color=(116, 72, 190),
        size=18, stun=0, blocked_by_obstacles=True, max_distance=620
    ):
        super().__init__()
        self.pos = pygame.Vector2(pos)
        self.start_pos = pygame.Vector2(pos)
        direction = safe_normalize(pygame.Vector2(target_pos) - self.pos)
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        self.velocity = direction * speed
        self.damage = damage
        self.stun = stun
        self.blocked_by_obstacles = blocked_by_obstacles
        self.max_distance = max_distance
        self.life = 4.0
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (size // 2, size // 2), size // 2 - 1)
        pygame.draw.circle(self.image, (235, 225, 255), (size // 2, size // 2), max(3, size // 4))
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt, obstacles=None):
        self.life -= dt
        old_pos = pygame.Vector2(self.pos)
        self.pos += self.velocity * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        hit_obstacle = any(
            self.rect.colliderect(getattr(obstacle, "collision_rect", obstacle.rect))
            for obstacle in obstacles or []
        )
        if self.blocked_by_obstacles and (hit_obstacle or is_line_blocked(old_pos, self.pos, obstacles)):
            self.kill()
            return
        if self.pos.distance_to(self.start_pos) > self.max_distance:
            self.kill()
            return
        if self.life <= 0:
            self.kill()
