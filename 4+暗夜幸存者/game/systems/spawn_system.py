import random

import pygame

from config import settings
from game_objects.enemy import Enemy
from utils.math_utils import random_spawn_position


class SpawnSystem:
    def __init__(self, enemy_config, difficulty=None):
        self.enemy_config = enemy_config
        self.difficulty = difficulty or {"enemy_hp": 1, "enemy_speed": 1, "enemy_damage": 1, "spawn_rate": 1}
        self.timer = 0
        self.small_boss_times = {
            5 * 60: ("blood_guardian", False),
            12 * 60: ("grave_warden", False),
            17 * 60: ("bone_harvester", False),
        }
        self.final_boss_spawned = False

    def update(self, dt, game_time, player, enemies, assets, obstacles=None):
        spawned = []
        if len(enemies) >= settings.MAX_ENEMIES:
            return spawned

        for boss_time, (enemy_id, done) in list(self.small_boss_times.items()):
            if game_time >= boss_time and not done:
                self.small_boss_times[boss_time] = (enemy_id, True)
                spawned.append(self.spawn_enemy(enemy_id, game_time, player, enemies, assets, obstacles, boss_scale=1.0))
        if game_time >= settings.FINAL_BOSS_TIME and not self.final_boss_spawned:
            self.final_boss_spawned = True
            spawned.append(self.spawn_enemy("vampire_count", game_time, player, enemies, assets, obstacles, boss_scale=1.0))

        self.timer -= dt
        if self.timer <= 0:
            count = self.spawn_count(game_time)
            for _ in range(count):
                enemy_id = self.pick_enemy(game_time)
                spawned.append(self.spawn_enemy(enemy_id, game_time, player, enemies, assets, obstacles))
            self.timer = self.spawn_interval(game_time)

        return spawned

    def spawn_interval(self, game_time):
        minute = game_time / 60
        return max(0.12, (1.08 - minute * 0.07) / self.difficulty.get("spawn_rate", 1))

    def spawn_count(self, game_time):
        minute = game_time / 60
        extra = 1 if minute >= 10 else 0
        return min(12, 1 + int(minute / 2.1) + extra)

    def pick_enemy(self, game_time):
        minute = game_time / 60
        elite_pool = []
        if game_time >= 5 * 60:
            elite_pool.extend(["giant_bat", "armored_zombie"])
        if game_time >= 12 * 60:
            elite_pool.append("necromancer")
        elite_chance = 0
        if game_time >= 5 * 60:
            elite_chance = min(0.38, 0.06 + (minute - 5) * 0.022)
        if elite_pool and random.random() < elite_chance:
            weights = [self.enemy_config[enemy_id]["weight"] for enemy_id in elite_pool]
            return random.choices(elite_pool, weights=weights, k=1)[0]

        if game_time < 5 * 60:
            pool = ["bat", "zombie", "skeleton"]
        elif game_time < 12 * 60:
            pool = ["bat", "zombie", "skeleton", "ghost"]
        else:
            pool = ["bat", "zombie", "skeleton", "ghost"]
        weights = [self.enemy_config[enemy_id]["weight"] for enemy_id in pool]
        return random.choices(pool, weights=weights, k=1)[0]

    def spawn_enemy(self, enemy_id, game_time, player, enemies, assets, obstacles=None, boss_scale=1.0):
        minute = game_time / 60
        player_level = max(1, getattr(player, "level", 1))
        hp_scale = 1 + minute * 0.095 + min(0.8, (player_level - 1) * 0.025)
        speed_scale = 1 + min(0.35, minute * 0.012)
        damage_scale = 1 + min(0.55, (player_level - 1) * 0.015)
        if self.enemy_config[enemy_id].get("boss"):
            hp_scale = boss_scale
            speed_scale = 1
            damage_scale = 1 + min(0.35, (player_level - 1) * 0.012)
        hp_scale *= self.difficulty.get("enemy_hp", 1)
        speed_scale *= self.difficulty.get("enemy_speed", 1)
        pos = self.safe_spawn_position(enemy_id, player, obstacles)
        enemy = Enemy(enemy_id, self.enemy_config[enemy_id], pos, assets.get(enemy_id), hp_scale, speed_scale)
        enemy.damage = int(enemy.damage * damage_scale * self.difficulty.get("enemy_damage", 1))
        enemies.add(enemy)
        return enemy

    def safe_spawn_position(self, enemy_id, player, obstacles=None):
        obstacles = obstacles or []
        radius = self.enemy_config[enemy_id].get("radius", 20)
        best_pos = None
        best_score = -1

        for _ in range(80):
            pos = random_spawn_position(player.pos, settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT, settings.SPAWN_PADDING)
            if not self.too_close_to_obstacle(pos, radius, obstacles):
                return pos

            # 如果当前点不合格，也记录一下距离障碍物最远的点，作为最后兜底。
            score = self.obstacle_clearance_score(pos, radius, obstacles)
            if score > best_score:
                best_pos = pos
                best_score = score

        # 极端情况下周围障碍物太密，就选重试中最不容易卡住的点。
        return best_pos or random_spawn_position(player.pos, settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT, settings.SPAWN_PADDING)

    def make_spawn_rect(self, pos, radius):
        spawn_rect = pygame.Rect(0, 0, radius * 2 + 22, radius * 2 + 22)
        spawn_rect.center = (round(pos.x), round(pos.y))
        return spawn_rect

    def too_close_to_obstacle(self, pos, radius, obstacles):
        spawn_rect = self.make_spawn_rect(pos, radius)
        for obstacle in obstacles:
            # 多留一圈安全距离，避免敌人出生在墓碑、树或墙边后第一帧就被卡住。
            safe_rect = obstacle.collision_rect.inflate(160, 160)
            if spawn_rect.colliderect(safe_rect):
                return True
        return False

    def obstacle_clearance_score(self, pos, radius, obstacles):
        if not obstacles:
            return 999999

        spawn_rect = self.make_spawn_rect(pos, radius)
        overlap_penalty = 0
        nearest_gap = 999999
        for obstacle in obstacles:
            safe_rect = obstacle.collision_rect.inflate(160, 160)
            if spawn_rect.colliderect(safe_rect):
                overlap = spawn_rect.clip(safe_rect)
                overlap_penalty += overlap.width * overlap.height
                continue
            dx = max(safe_rect.left - spawn_rect.right, spawn_rect.left - safe_rect.right, 0)
            dy = max(safe_rect.top - spawn_rect.bottom, spawn_rect.top - safe_rect.bottom, 0)
            score = dx * dx + dy * dy
            nearest_gap = min(nearest_gap, score)
        if overlap_penalty:
            return -overlap_penalty
        return nearest_gap
