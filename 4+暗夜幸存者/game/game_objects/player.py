import pygame

from config import settings
from game_objects.weapon import Weapon
from utils.math_utils import safe_normalize


class Player(pygame.sprite.Sprite):
    def __init__(self, character_id, data, weapon_data, save_bonus, image=None):
        super().__init__()
        self.character_id = character_id
        self.name = data["name"]
        self.base_data = data

        self.max_hp = data["max_hp"] + save_bonus.get("max_hp", 0)
        self.hp = self.max_hp
        self.speed = data["speed"] + save_bonus.get("speed", 0)
        self.damage_bonus = data["damage_bonus"] + save_bonus.get("damage", 0)
        self.cooldown_bonus = data["cooldown_bonus"]
        self.pickup_range = data["pickup_range"] + save_bonus.get("pickup", 0)
        self.armor = data.get("armor", 0)
        self.luck = 0

        self.level = 1
        self.exp = 0
        self.next_exp = 20
        self.kill_count = 0
        self.coins_earned = 0
        self.hit_timer = 0
        self.hit_flash_timer = 0
        self.stun_timer = 0
        self.stun_immunity_timer = 0
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.dash_duration = 0.16
        self.dash_speed = 820
        self.dash_cooldown_time = 3.5
        self.invincible_timer = 0
        self.last_direction = pygame.Vector2(1, 0)

        self.pos = pygame.Vector2(0, 0)
        self.image = image if image else self.make_fallback_image()
        self.rect = self.image.get_rect(center=self.pos)
        self.collision_rect = self.make_collision_rect()
        self.collision_radius = max(self.collision_rect.width, self.collision_rect.height) * 0.52

        self.weapons = [Weapon(data["start_weapon"], weapon_data[data["start_weapon"]])]
        self.passives = {}
        self.active_items = {}
        self.temp_damage_bonus = 0
        self.spinach_timer = 0
        self.spinach_duration = 0

    def make_fallback_image(self):
        surface = pygame.Surface((42, 42), pygame.SRCALPHA)
        pygame.draw.circle(surface, (198, 46, 72), (21, 21), 19)
        pygame.draw.circle(surface, (248, 232, 202), (21, 16), 8)
        pygame.draw.rect(surface, (45, 39, 58), (12, 22, 18, 14), border_radius=4)
        return surface

    def make_collision_rect(self):
        width = max(18, int(self.rect.width * 0.60))
        height = max(20, int(self.rect.height * 0.65))
        rect = pygame.Rect(0, 0, width, height)
        rect.center = self.rect.center
        return rect

    def sync_collision_rect(self):
        self.collision_rect.center = self.rect.center
        self.pos.x = self.rect.centerx
        self.pos.y = self.rect.centery

    def update(self, dt, keys, obstacles):
        self.update_timers(dt)

        direction = pygame.Vector2()
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            direction.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            direction.x += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            direction.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            direction.y += 1

        if direction.length_squared() > 0:
            self.last_direction = safe_normalize(direction)

        # 眩晕时不能移动；冲刺会覆盖普通移动，并提供很短的无敌窗口。
        if self.stun_timer > 0:
            move = pygame.Vector2()
        elif self.dash_timer > 0:
            move = self.last_direction * self.dash_speed * dt
        else:
            move = safe_normalize(direction) * self.speed * dt
        self.move_with_obstacles(move, obstacles)

    def update_timers(self, dt):
        if self.hit_timer > 0:
            self.hit_timer -= dt
        if self.hit_flash_timer > 0:
            self.hit_flash_timer = max(0, self.hit_flash_timer - dt)
        if self.stun_timer > 0:
            self.stun_timer = max(0, self.stun_timer - dt)
            if self.stun_timer == 0:
                self.stun_immunity_timer = 0.8
        elif self.stun_immunity_timer > 0:
            self.stun_immunity_timer = max(0, self.stun_immunity_timer - dt)
        if self.dash_timer > 0:
            self.dash_timer = max(0, self.dash_timer - dt)
        if self.dash_cooldown > 0:
            self.dash_cooldown = max(0, self.dash_cooldown - dt)
        if self.invincible_timer > 0:
            self.invincible_timer = max(0, self.invincible_timer - dt)
        if self.spinach_timer > 0:
            self.spinach_timer -= dt
            if self.spinach_timer <= 0:
                self.temp_damage_bonus = 0
                self.spinach_timer = 0

    def move_with_obstacles(self, move, obstacles):
        # 分轴移动可以减少角色卡在障碍物角落的情况。
        self.pos.x += move.x
        self.rect.centerx = round(self.pos.x)
        self.collision_rect.centerx = self.rect.centerx
        for obstacle in obstacles:
            if self.collision_rect.colliderect(obstacle.collision_rect):
                if move.x > 0:
                    self.collision_rect.right = obstacle.collision_rect.left
                elif move.x < 0:
                    self.collision_rect.left = obstacle.collision_rect.right
                self.rect.centerx = self.collision_rect.centerx
                self.pos.x = self.rect.centerx

        self.pos.y += move.y
        self.rect.centery = round(self.pos.y)
        self.collision_rect.centery = self.rect.centery
        for obstacle in obstacles:
            if self.collision_rect.colliderect(obstacle.collision_rect):
                if move.y > 0:
                    self.collision_rect.bottom = obstacle.collision_rect.top
                elif move.y < 0:
                    self.collision_rect.top = obstacle.collision_rect.bottom
                self.rect.centery = self.collision_rect.centery
                self.pos.y = self.rect.centery

        self.sync_collision_rect()

    def take_damage(self, amount):
        if self.invincible_timer > 0:
            return
        if self.hit_timer > 0:
            return
        real_damage = max(1, amount - self.armor)
        self.hp -= real_damage
        self.hit_timer = settings.PLAYER_HIT_COOLDOWN
        self.hit_flash_timer = 0.16

    def apply_stun(self, duration):
        if self.invincible_timer > 0 or self.stun_immunity_timer > 0:
            return False
        self.stun_timer = max(self.stun_timer, duration)
        self.dash_timer = 0
        return True

    def start_dash(self):
        if self.stun_timer > 0 or self.dash_cooldown > 0:
            return False
        self.dash_timer = self.dash_duration
        self.dash_cooldown = self.dash_cooldown_time
        self.invincible_timer = 0.18
        return True

    def can_attack(self):
        return self.stun_timer <= 0

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def add_exp(self, amount):
        self.exp += amount
        leveled = False
        while self.exp >= self.next_exp:
            self.exp -= self.next_exp
            self.level += 1
            self.next_exp = int(self.next_exp * 1.18 + 12)
            leveled = True
        return leveled

    def get_weapon(self, weapon_id):
        for weapon in self.weapons:
            if weapon.weapon_id == weapon_id:
                return weapon
        return None

    def add_or_upgrade_weapon(self, weapon_id, weapon_config):
        weapon = self.get_weapon(weapon_id)
        if weapon:
            weapon.level_up()
            return
        self.weapons.append(Weapon(weapon_id, weapon_config))

    def add_or_upgrade_passive(self, passive_id, passive_config):
        level = self.passives.get(passive_id, 0) + 1
        self.passives[passive_id] = min(level, passive_config["max_level"])
        if "damage_bonus" in passive_config:
            self.damage_bonus += passive_config["damage_bonus"]
        if "armor" in passive_config:
            self.armor += passive_config["armor"]
        if "pickup_range" in passive_config:
            self.pickup_range += passive_config["pickup_range"]
        if "luck" in passive_config:
            self.luck += passive_config["luck"]

    def add_active_item(self, item_id, item_config):
        count = self.active_items.get(item_id, 0)
        self.active_items[item_id] = min(count + 1, item_config["max_stack"])

    def use_active_item(self, item_id, item_config):
        count = self.active_items.get(item_id, 0)
        if count <= 0:
            return False
        self.active_items[item_id] = count - 1
        if "damage_bonus" in item_config:
            self.temp_damage_bonus = max(self.temp_damage_bonus, item_config["damage_bonus"])
            self.spinach_duration = item_config.get("duration", 8)
            self.spinach_timer = self.spinach_duration
        return True

    def total_damage_bonus(self):
        return self.damage_bonus + self.temp_damage_bonus

    def spinach_ratio(self):
        if self.spinach_duration <= 0:
            return 0
        return max(0, min(1, self.spinach_timer / self.spinach_duration))

    def evolve_weapon(self, old_id, new_id, new_config):
        evolved = self.get_weapon(new_id)
        if evolved:
            evolved.level_up()
            self.weapons = [w for w in self.weapons if w.weapon_id != old_id]
            return f"{evolved.name} 提升到 Lv.{evolved.level}"
        old_weapon = self.get_weapon(old_id)
        old_name = old_weapon.name if old_weapon else new_config["name"]
        self.weapons = [w for w in self.weapons if w.weapon_id != old_id]
        self.weapons.append(Weapon(new_id, new_config))
        return f"{old_name} 进化为 {new_config['name']}！"

    def is_dead(self):
        return self.hp <= 0
