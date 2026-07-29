import math
import random

import pygame

from game_objects.enemy import EnemyProjectile
from game_objects.enemy_attack import EnemyAttack, line_attack_between
from utils.math_utils import safe_normalize


class EnemySkillSystem:
    """集中管理敌人特殊技能，避免主循环里写太多敌人行为细节。"""

    def __init__(self):
        self.shadow_timer = 6.0

    def update(self, dt, game_time, player, enemies, enemy_attacks, enemy_projectiles):
        self.update_shadow_corrosion(dt, game_time, player, enemy_attacks)
        speed_up = 1 + min(0.75, max(0, game_time - 10 * 60) / 600)
        stun_warning_count = sum(1 for attack in enemy_attacks if getattr(attack, "stun", 0) > 0)

        for enemy in list(enemies):
            skills = enemy.data.get("skills", [])
            if not skills or not enemy.alive():
                continue
            enemy.skill_timer -= dt * speed_up
            if enemy.skill_timer > 0:
                continue
            if enemy.pos.distance_to(player.pos) > enemy.data.get("skill_range", 660):
                continue
            choices = list(skills)
            if stun_warning_count >= 4:
                choices = [skill for skill in choices if skill not in ("charge", "stomp", "shield_charge", "chains")]
            if not choices:
                continue
            chosen = random.choice(choices)
            self.cast_skill(enemy, chosen, player, enemy_attacks, enemy_projectiles, game_time)
            if chosen in ("charge", "stomp", "shield_charge", "chains"):
                stun_warning_count += 1
            cooldown = enemy.data.get("skill_cooldown", 5.0)
            enemy.skill_timer = cooldown * random.uniform(0.85, 1.25)

    def update_shadow_corrosion(self, dt, game_time, player, enemy_attacks):
        if game_time < 15 * 60:
            return
        self.shadow_timer -= dt
        active_shadow = sum(1 for attack in enemy_attacks if getattr(attack, "source", "") == "shadow")
        if self.shadow_timer > 0 or active_shadow >= 3:
            return
        angle = random.uniform(0, math.tau)
        distance = random.randint(90, 260)
        pos = player.pos + pygame.Vector2(math.cos(angle), math.sin(angle)) * distance
        attack = EnemyAttack(
            pos, "circle", 8 + int(game_time / 240), 1.2, 4.0,
            radius=92, color=(155, 48, 174), repeat=True, hit_interval=0.75
        )
        attack.source = "shadow"
        enemy_attacks.add(attack)
        self.shadow_timer = max(2.8, 5.5 - (game_time - 15 * 60) / 180)

    def cast_skill(self, enemy, skill, player, enemy_attacks, enemy_projectiles, game_time):
        if skill == "charge":
            self.cast_charge(enemy, player, enemy_attacks, stun=0.75)
        elif skill == "stomp":
            self.cast_stomp(enemy, enemy_attacks)
        elif skill == "blink":
            self.cast_blink(enemy, player, enemy_attacks)
        elif skill == "bone_spread":
            self.cast_bone_spread(enemy, player, enemy_projectiles, game_time)
        elif skill == "laser":
            self.cast_laser(enemy, player, enemy_attacks)
        elif skill == "shield_charge":
            self.cast_charge(enemy, player, enemy_attacks, stun=1.0, width=72, speed=610)
        elif skill == "chains":
            self.cast_chains(enemy, player, enemy_attacks)
        elif skill == "big_explosion":
            self.cast_big_explosion(enemy, player, enemy_attacks)
        elif skill == "ring_shots":
            self.cast_ring_shots(enemy, enemy_projectiles)

    def cast_charge(self, enemy, player, enemy_attacks, stun=0.75, width=54, speed=560):
        direction = safe_normalize(player.pos - enemy.pos)
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        enemy.start_charge(direction, speed=speed)
        attack = line_attack_between(
            enemy.pos, enemy.pos + direction * 380,
            enemy.damage * 1.1, 0.72, 0.26, width, stun=stun, color=(225, 62, 82)
        )
        enemy_attacks.add(attack)

    def cast_stomp(self, enemy, enemy_attacks):
        enemy_attacks.add(EnemyAttack(
            enemy.pos, "circle", enemy.damage * 1.05, 0.82, 0.25,
            radius=112, color=(230, 116, 55), stun=0.9
        ))

    def cast_blink(self, enemy, player, enemy_attacks):
        direction = safe_normalize(enemy.pos - player.pos)
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        target = player.pos + direction * 78
        enemy.start_teleport(target)
        enemy_attacks.add(EnemyAttack(
            target, "circle", enemy.damage, 0.62, 0.18,
            radius=56, color=(148, 112, 222)
        ))

    def cast_bone_spread(self, enemy, player, enemy_projectiles, game_time):
        base = safe_normalize(player.pos - enemy.pos)
        if base.length_squared() == 0:
            base = pygame.Vector2(1, 0)
        base_angle = math.atan2(base.y, base.x)
        offsets = self.bone_spike_offsets(game_time)
        for offset in offsets:
            direction = pygame.Vector2(math.cos(base_angle + offset), math.sin(base_angle + offset))
            enemy_projectiles.add(EnemyProjectile(
                enemy.pos + direction * 24, enemy.pos + direction * 200,
                max(3, int(enemy.damage * 0.6)), 330, color=(220, 214, 190),
                size=14, blocked_by_obstacles=True, max_distance=enemy.data.get("bone_range", 520)
            ))

    def bone_spike_offsets(self, game_time):
        if game_time >= 15 * 60:
            return (-0.32, -0.16, 0, 0.16, 0.32)
        if game_time >= 10 * 60:
            return (-0.22, 0, 0.22)
        if game_time >= 5 * 60:
            return (-0.12, 0.12)
        return (0,)

    def cast_laser(self, enemy, player, enemy_attacks):
        enemy_attacks.add(line_attack_between(
            enemy.pos, player.pos, enemy.damage * 1.25, 0.95, 0.24, 34,
            color=(142, 88, 225)
        ))

    def cast_chains(self, enemy, player, enemy_attacks):
        for angle in (0, math.tau / 3, math.tau * 2 / 3):
            pos = player.pos + pygame.Vector2(math.cos(angle), math.sin(angle)) * 86
            enemy_attacks.add(EnemyAttack(
                pos, "circle", max(4, enemy.damage * 0.55), 0.95, 0.2,
                radius=48, color=(86, 146, 225), stun=0.8,
                source_pos=enemy.pos, blocked_by_obstacles=True
            ))

    def cast_big_explosion(self, enemy, player, enemy_attacks):
        enemy_attacks.add(EnemyAttack(
            player.pos, "circle", enemy.damage * 1.55, 1.25, 0.32,
            radius=145, color=(225, 55, 70)
        ))

    def cast_ring_shots(self, enemy, enemy_projectiles):
        for index in range(12):
            angle = math.tau * index / 12
            direction = pygame.Vector2(math.cos(angle), math.sin(angle))
            enemy_projectiles.add(EnemyProjectile(
                enemy.pos + direction * 34, enemy.pos + direction * 260,
                max(4, int(enemy.damage * 0.45)), 290, color=(190, 60, 100),
                size=15, max_distance=enemy.data.get("ring_range", 520)
            ))
