import random

import pygame

from game_objects.item import DropItem
from utils.math_utils import is_line_blocked


class CollisionSystem:
    def handle_player_enemy(self, player, enemies, enemy_projectiles=None):
        for enemy in enemies:
            if self.enemy_hits_player(enemy, player):
                player.take_damage(enemy.damage)
        if enemy_projectiles is not None:
            for bullet in list(enemy_projectiles):
                if not self.projectile_hits_player(bullet, player):
                    continue
                bullet.kill()
                player.take_damage(bullet.damage)
                if getattr(bullet, "stun", 0) > 0:
                    player.apply_stun(bullet.stun)

    def handle_enemy_attacks(self, player, enemy_attacks, obstacles=None):
        for attack in list(enemy_attacks):
            if getattr(attack, "blocked_by_obstacles", False):
                source_pos = getattr(attack, "source_pos", attack.pos)
                if is_line_blocked(source_pos, player.collision_rect.center, obstacles):
                    attack.kill()
                    continue
            if not attack.can_hit() or not attack.collides_player(player):
                continue
            player.take_damage(attack.damage)
            if attack.stun > 0:
                player.apply_stun(attack.stun)
            attack.mark_hit()

    def handle_projectiles(self, player, projectiles, area_effects, enemies, drops, obstacles=None):
        for projectile in list(projectiles):
            hits = pygame.sprite.spritecollide(projectile, enemies, False, pygame.sprite.collide_circle)
            for enemy in hits:
                if id(enemy) in projectile.hit_enemies:
                    continue
                projectile.hit_enemies.add(id(enemy))
                dead = enemy.take_damage(projectile.damage)
                if projectile.life_steal:
                    player.heal(projectile.life_steal)
                if dead:
                    self.kill_enemy(player, enemy, drops)
                projectile.pierce -= 1
                if projectile.pierce <= 0:
                    projectile.kill()
                    break

        for effect in list(area_effects):
            for enemy in list(enemies):
                if id(enemy) in effect.hit_enemies:
                    continue
                if not self.area_hits_enemy(effect, enemy):
                    continue
                target_enemy_ids = getattr(effect, "target_enemy_ids", None)
                if target_enemy_ids is not None and id(enemy) not in target_enemy_ids:
                    continue
                if getattr(effect, "blocked_by_obstacles", False) and is_line_blocked(effect.pos, enemy.pos, obstacles):
                    continue
                effect.hit_enemies.add(id(enemy))
                dead = enemy.take_damage(effect.damage)
                if effect.life_steal:
                    player.heal(effect.life_steal)
                if dead:
                    self.kill_enemy(player, enemy, drops)

    def area_hits_enemy(self, effect, enemy):
        enemy_radius = getattr(enemy, "radius", max(enemy.rect.width, enemy.rect.height) * 0.5)
        return effect.pos.distance_to(enemy.pos) <= effect.radius + enemy_radius

    def enemy_hits_player(self, enemy, player):
        player_pos = pygame.Vector2(player.collision_rect.center)
        enemy_radius = getattr(enemy, "radius", max(enemy.rect.width, enemy.rect.height) * 0.5)
        return player_pos.distance_to(enemy.pos) <= player.collision_radius + enemy_radius

    def projectile_hits_player(self, projectile, player):
        player_pos = pygame.Vector2(player.collision_rect.center)
        projectile_radius = max(projectile.rect.width, projectile.rect.height) * 0.5
        return player_pos.distance_to(projectile.pos) <= player.collision_radius + projectile_radius

    def kill_enemy(self, player, enemy, drops):
        player.kill_count += 1
        player.coins_earned += enemy.coin
        drops.add(DropItem("exp", enemy.pos, enemy.exp))
        if enemy.is_boss or (enemy.is_elite and random.random() < 0.06):
            drops.add(DropItem("chest", enemy.pos + pygame.Vector2(18, -10), 1))
        if random.random() < 0.025:
            drops.add(DropItem("heart", enemy.pos + pygame.Vector2(-14, 12), 25))
        if random.random() < 0.018:
            drops.add(DropItem("spinach_can", enemy.pos + pygame.Vector2(12, 14), 1))
        enemy.kill()

    def handle_drops(self, player, drops, active_items_config=None):
        leveled = False
        active_items_config = active_items_config or {}
        for item in list(drops):
            distance = item.pos.distance_to(player.pos)
            if distance <= player.pickup_range:
                item.move_towards(player.pos, 1 / 60)
            if distance <= 28:
                if item.kind == "exp":
                    leveled = player.add_exp(item.value) or leveled
                elif item.kind == "heart":
                    player.heal(item.value)
                elif item.kind == "chest":
                    player.coins_earned += 25
                    leveled = True
                elif item.kind in active_items_config:
                    player.add_active_item(item.kind, active_items_config[item.kind])
                item.kill()
        return leveled
