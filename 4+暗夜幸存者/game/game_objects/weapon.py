import math
import random

import pygame

from utils.math_utils import is_line_blocked, safe_normalize


class Projectile(pygame.sprite.Sprite):
    def __init__(
        self, pos, velocity, damage, max_distance, pierce, color,
        size=12, life_steal=0, homing=False, target=None, speed=520
    ):
        super().__init__()
        self.pos = pygame.Vector2(pos)
        self.start_pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(velocity)
        self.speed = speed
        self.damage = damage
        self.max_distance = max_distance
        self.pierce = pierce
        self.life_steal = life_steal
        self.homing = homing
        self.target = target
        self.hit_enemies = set()

        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (size // 2, size // 2), size // 2)
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt, obstacles=None):
        if self.homing and self.target and self.target.alive():
            direction = safe_normalize(self.target.pos - self.pos)
            if direction.length_squared() > 0:
                # 追踪弹不是瞬间拐弯，保留一点飞行手感。
                desired = direction * self.speed
                self.velocity = self.velocity.lerp(desired, min(1, dt * 7.5))
        old_pos = pygame.Vector2(self.pos)
        self.pos += self.velocity * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        hit_obstacle = any(
            self.rect.colliderect(getattr(obstacle, "collision_rect", obstacle.rect))
            for obstacle in obstacles or []
        )
        if hit_obstacle or is_line_blocked(old_pos, self.pos, obstacles):
            self.kill()
            return
        if self.pos.distance_to(self.start_pos) > self.max_distance:
            self.kill()


class AreaEffect(pygame.sprite.Sprite):
    def __init__(
        self, pos, radius, damage, duration, color, life_steal=0,
        blocked_by_obstacles=False, target_enemy_ids=None
    ):
        super().__init__()
        self.pos = pygame.Vector2(pos)
        self.radius = radius
        self.damage = damage
        self.duration = duration
        self.life_steal = life_steal
        self.blocked_by_obstacles = blocked_by_obstacles
        self.target_enemy_ids = target_enemy_ids
        self.hit_enemies = set()

        size = radius * 2
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius, 3)
        pygame.draw.circle(self.image, (*color[:3], 45), (radius, radius), radius)
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt):
        self.duration -= dt
        if self.duration <= 0:
            self.kill()


class Weapon:
    def __init__(self, weapon_id, config):
        self.weapon_id = weapon_id
        self.config = config
        self.level = 1
        self.timer = random.uniform(0, 0.2)
        self.orbit_angle = 0

    @property
    def name(self):
        return self.config["name"]

    def level_up(self):
        self.level = min(self.level + 1, self.config["max_level"])

    def scaled(self, key, default=0):
        base = self.config.get(key, default)
        if key == "damage":
            return base * (1 + (self.level - 1) * 0.22)
        if key == "cooldown":
            return max(0.12, base * (1 - (self.level - 1) * 0.045))
        if key in ("range", "target_range"):
            return base * (1 + (self.level - 1) * 0.08)
        if key == "amount":
            return int(base + (self.level - 1) // 2)
        if key == "pierce":
            return int(base + (self.level - 1) // 3)
        return base

    def update(self, dt, player, enemies, projectiles, area_effects, obstacles=None):
        if hasattr(player, "can_attack") and not player.can_attack():
            return
        self.timer -= dt
        if self.config["kind"] == "orbit":
            self.orbit_angle += dt * (2.8 + self.level * 0.15)
            if self.timer <= 0:
                self.fire_orbit(player, enemies, area_effects, obstacles)
                self.timer = self.scaled("cooldown") * player.cooldown_bonus
            return

        if self.timer > 0 or not enemies:
            return

        target = self.find_target(player.pos, enemies)
        if not target:
            return

        kind = self.config["kind"]
        if kind == "melee":
            self.fire_melee(player, target, area_effects, obstacles)
        elif kind == "projectile":
            self.fire_projectile(player, target, projectiles)
        elif kind == "explosion":
            self.fire_explosion(player, target, area_effects)
        elif kind == "lightning":
            self.fire_lightning(player, enemies, area_effects)

        self.timer = self.scaled("cooldown") * player.cooldown_bonus

    def find_target(self, player_pos, enemies):
        living = [enemy for enemy in enemies if enemy.alive()]
        target_range = self.scaled("target_range", 0)
        if target_range > 0:
            living = [
                enemy for enemy in living
                if enemy.pos.distance_to(player_pos) <= target_range
            ]
        if not living:
            return None
        return min(living, key=lambda enemy: enemy.pos.distance_squared_to(player_pos))

    def damage_value(self, player):
        bonus = player.total_damage_bonus() if hasattr(player, "total_damage_bonus") else player.damage_bonus
        return int(self.scaled("damage") * bonus)

    def fire_melee(self, player, target, area_effects, obstacles=None):
        amount = self.scaled("amount", 1)
        direction = safe_normalize(target.pos - player.pos)
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        for index in range(amount):
            angle = math.atan2(direction.y, direction.x) + (index - amount // 2) * 0.55
            offset = pygame.Vector2(math.cos(angle), math.sin(angle)) * (self.scaled("range") * 0.55)
            effect_pos = player.pos + offset
            if is_line_blocked(effect_pos, target.pos, obstacles):
                continue
            effect = AreaEffect(
                effect_pos,
                int(self.scaled("range") * 0.58),
                self.damage_value(player),
                0.18,
                (220, 70, 92, 145),
                self.config.get("life_steal", 0),
                blocked_by_obstacles=True,
            )
            area_effects.add(effect)

    def fire_projectile(self, player, target, projectiles):
        amount = self.scaled("amount", 1)
        base_dir = safe_normalize(target.pos - player.pos)
        if base_dir.length_squared() == 0:
            base_dir = pygame.Vector2(1, 0)
        for index in range(amount):
            spread = (index - (amount - 1) / 2) * 0.13
            angle = math.atan2(base_dir.y, base_dir.x) + spread
            direction = pygame.Vector2(math.cos(angle), math.sin(angle))
            color = (230, 230, 210) if "knife" in self.weapon_id or "blade" in self.weapon_id else (100, 170, 245)
            projectile = Projectile(
                player.pos + direction * 26,
                direction * self.scaled("speed", 520),
                self.damage_value(player),
                self.scaled("range", 650),
                self.scaled("pierce", 1),
                color,
                13 if self.weapon_id != "thousand_blades" else 10,
                homing=self.config.get("homing", False),
                target=target if self.config.get("homing", False) else None,
                speed=self.scaled("speed", 520),
            )
            projectiles.add(projectile)

    def fire_explosion(self, player, target, area_effects):
        effect = AreaEffect(
            target.pos,
            int(self.scaled("range", 120)),
            self.damage_value(player),
            0.28,
            (236, 104, 54, 150),
        )
        area_effects.add(effect)

    def fire_lightning(self, player, enemies, area_effects):
        target_range = self.scaled("target_range", 620)
        in_range = [enemy for enemy in enemies if enemy.pos.distance_to(player.pos) < target_range]
        random.shuffle(in_range)
        for enemy in in_range[: self.scaled("amount", 1)]:
            effect = AreaEffect(
                enemy.pos,
                int(self.scaled("range", 110)),
                self.damage_value(player),
                0.2,
                (95, 190, 245, 150),
                target_enemy_ids={id(enemy)},
            )
            area_effects.add(effect)

    def fire_orbit(self, player, enemies, area_effects, obstacles=None):
        amount = self.scaled("amount", 2)
        radius = self.scaled("range", 90)
        for index in range(amount):
            angle = self.orbit_angle + math.tau * index / amount
            pos = player.pos + pygame.Vector2(math.cos(angle), math.sin(angle)) * radius
            nearby = [
                enemy for enemy in enemies
                if enemy.alive() and enemy.pos.distance_to(pos) <= 80
            ]
            if nearby and not any(not is_line_blocked(pos, enemy.pos, obstacles) for enemy in nearby):
                continue
            effect = AreaEffect(
                pos, 24, self.damage_value(player), 0.18, (232, 214, 136, 150),
                blocked_by_obstacles=True
            )
            area_effects.add(effect)
