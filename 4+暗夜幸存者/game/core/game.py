import json
import os

import pygame

from config import settings
from core.scene_manager import SceneManager
from game_objects.enemy import EnemyProjectile
from game_objects.obstacle import make_obstacles
from game_objects.player import Player
from systems.collision_system import CollisionSystem
from systems.enemy_skill_system import EnemySkillSystem
from systems.save_system import SaveSystem
from systems.shop_system import ShopSystem
from systems.spawn_system import SpawnSystem
from systems.upgrade_system import UpgradeSystem
from ui.widgets import draw_bar, draw_panel
from utils.resource_path import resource_path


class Game:
    def __init__(self):
        # mixer 必须尽量在 pygame.init 前设置，否则部分设备会有延迟。
        try:
            pygame.mixer.pre_init(44100, -16, 2, 512)
        except pygame.error:
            pass
        pygame.init()
        pygame.display.set_caption(settings.GAME_TITLE)
        try:
            icon = pygame.image.load(resource_path("resources/images/app_icon.png")).convert_alpha()
            pygame.display.set_icon(icon)
        except (pygame.error, FileNotFoundError):
            pass
        self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.characters = self.load_json("config/characters.json")
        self.weapons_config = self.load_json("config/weapons.json")
        self.passives_config = self.load_json("config/passives.json")
        self.active_items_config = self.load_json("config/active_items.json")
        self.enemies_config = self.load_json("config/enemies.json")
        self.shop_config = self.load_json("config/shop.json")
        self.difficulties = self.load_json("config/difficulties.json")

        self.save_system = SaveSystem()
        self.shop_system = ShopSystem(self.save_system, self.characters, self.weapons_config, self.shop_config)
        self.scene = SceneManager()
        self.fonts = self.load_fonts()
        self.assets = self.load_assets()
        self.sounds = self.load_audio()

        self.selected_menu = 0
        self.selected_difficulty = 0
        self.selected_character = 0
        self.selected_shop = 0
        self.selected_upgrade = 0
        self.selected_bestiary_category = 0
        self.selected_bestiary_item = 0
        self.selected_pause = 0
        self.shop_message = ""
        self.main_message = ""
        self.main_message_timer = 0
        self.delete_save_rect = pygame.Rect(settings.SCREEN_WIDTH - 190, settings.SCREEN_HEIGHT - 64, 158, 42)
        self.pause_buttons = [
            ("继续", pygame.Rect(settings.SCREEN_WIDTH // 2 - 230, 390, 180, 54)),
            ("结束", pygame.Rect(settings.SCREEN_WIDTH // 2 + 50, 390, 180, 54)),
        ]
        self.result_saved = False
        self.last_result = {}
        self.selected_difficulty_id = "hard"
        self.current_music = None

        self.reset_run_data()

    def load_json(self, relative_path):
        path = resource_path(relative_path)
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    def load_fonts(self):
        # 优先加载明确的中文字体文件，避免 Pygame 默认字体无法显示中文。
        # 同时覆盖 Windows、macOS 和常见 Linux 字体路径。
        font_paths = [
            r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\simsun.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/System/Library/Fonts/Supplemental/Songti.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        ]
        fonts = {}
        for size_name, size in {"big": 56, "title": 34, "normal": 24, "small": 18}.items():
            font = None
            for path in font_paths:
                if os.path.exists(path):
                    try:
                        font = pygame.font.Font(path, size)
                        break
                    except pygame.error:
                        # 个别系统字体容器可能无法被当前 Pygame 读取，继续尝试下一项。
                        continue
            if font is None:
                # 最后的系统字体回退仍可能不支持中文，但不会让游戏启动失败。
                for font_name in ("notosanscjk", "hiraginosansgb", "stheiti", "simsun", "arialunicode"):
                    matched_path = pygame.font.match_font(font_name)
                    if matched_path:
                        try:
                            font = pygame.font.Font(matched_path, size)
                            break
                        except pygame.error:
                            continue
            if font is None:
                font = pygame.font.Font(None, size)
            fonts[size_name] = font
        return fonts

    def load_assets(self):
        images = {}
        image_dir = resource_path("resources/images")

        expected = [
            "hunter", "mage", "knight",
            "whip", "knife", "holy_book", "fire_staff", "magic_bolt", "lightning_ring",
            "blood_whip", "thousand_blades", "spinach_can",
            "hollow_sword", "armor", "focus_crystal", "clover", "cemetery_ground",
            *self.enemies_config.keys(),
        ]
        for name in expected:
            path = os.path.join(image_dir, f"{name}.png")
            images[name] = pygame.image.load(path).convert_alpha() if os.path.exists(path) else None

        tile_path = os.path.join(image_dir, "cemetery_ground.png")
        images["cemetery_tile"] = None
        if os.path.exists(tile_path):
            tile_image = pygame.image.load(tile_path).convert_alpha()
            images["cemetery_tile"] = pygame.transform.scale(tile_image, (settings.TILE_SIZE, settings.TILE_SIZE))
        return images

    def load_audio(self):
        sounds = {"enabled": False, "attack": None, "pickup": None, "boss": None, "music": {}}
        audio_dir = resource_path("resources/audio")
        if not pygame.mixer.get_init():
            return sounds
        try:
            for name in ("attack", "pickup", "boss"):
                path = os.path.join(audio_dir, f"{name}.wav")
                if os.path.exists(path):
                    sounds[name] = pygame.mixer.Sound(path)
            if sounds["attack"]:
                sounds["attack"].set_volume(0.18)
            if sounds["pickup"]:
                sounds["pickup"].set_volume(0.45)
            if sounds["boss"]:
                sounds["boss"].set_volume(0.55)
            for music_id in ("explore", "tense", "danger", "boss"):
                bgm_path = os.path.join(audio_dir, f"bgm_{music_id}.wav")
                if os.path.exists(bgm_path):
                    sounds["music"][music_id] = bgm_path
            sounds["enabled"] = True
        except pygame.error:
            sounds["enabled"] = False
        return sounds

    def play_sound(self, name):
        if self.sounds.get("enabled") and self.sounds.get(name):
            self.sounds[name].play()

    def switch_music(self, music_id):
        if not self.sounds.get("enabled") or self.current_music == music_id:
            return
        music_path = self.sounds.get("music", {}).get(music_id)
        if not music_path:
            return
        try:
            pygame.mixer.music.fadeout(180)
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(0.55)
            pygame.mixer.music.play(-1, fade_ms=300)
            self.current_music = music_id
        except pygame.error:
            pass

    def reset_run_data(self):
        self.player = None
        self.enemies = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.enemy_projectiles = pygame.sprite.Group()
        self.enemy_attacks = pygame.sprite.Group()
        self.area_effects = pygame.sprite.Group()
        self.drops = pygame.sprite.Group()
        self.obstacles = make_obstacles()
        difficulty = self.difficulties.get(self.selected_difficulty_id, self.difficulties["hard"])
        self.spawn_system = SpawnSystem(self.enemies_config, difficulty)
        self.collision_system = CollisionSystem()
        self.enemy_skill_system = EnemySkillSystem()
        self.upgrade_system = UpgradeSystem(self.weapons_config, self.passives_config, self.save_system)
        self.game_time = 0
        self.upgrade_options = []
        self.win = False
        self.final_boss = None
        self.seen_enemy_types = set()
        self.enemy_intro_popups = []
        self.evolution_popups = []

    def run(self):
        while self.running:
            raw_dt = self.clock.tick(settings.FPS) / 1000
            dt = min(raw_dt, 0.05)
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.handle_key(event.key, getattr(event, "unicode", ""))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_mouse_click(event.pos)

    def handle_mouse_click(self, pos):
        if self.scene.current == SceneManager.MAIN_MENU and self.delete_save_rect.collidepoint(pos):
            self.delete_save()
        elif self.scene.current == SceneManager.PAUSED:
            for index, (_text, rect) in enumerate(self.pause_buttons):
                if rect.collidepoint(pos):
                    self.selected_pause = index
                    self.confirm_pause_choice()
                    break

    def handle_key(self, key, text=""):
        if self.scene.current == SceneManager.MAIN_MENU:
            self.handle_vertical_menu(key, 4, "selected_menu")
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.selected_menu == 0:
                    self.scene.switch(SceneManager.DIFFICULTY_SELECT)
                elif self.selected_menu == 1:
                    self.scene.switch(SceneManager.SHOP)
                elif self.selected_menu == 2:
                    self.scene.switch(SceneManager.BESTIARY)
                else:
                    self.running = False
        elif self.scene.current == SceneManager.DIFFICULTY_SELECT:
            difficulty_ids = list(self.difficulties.keys())
            self.handle_vertical_menu(key, len(difficulty_ids), "selected_difficulty")
            if key == pygame.K_ESCAPE:
                self.scene.switch(SceneManager.MAIN_MENU)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                self.selected_difficulty_id = difficulty_ids[self.selected_difficulty]
                self.scene.switch(SceneManager.CHARACTER_SELECT)
        elif self.scene.current == SceneManager.CHARACTER_SELECT:
            character_ids = list(self.characters.keys())
            self.handle_vertical_menu(key, len(character_ids), "selected_character")
            if key == pygame.K_ESCAPE:
                self.scene.switch(SceneManager.DIFFICULTY_SELECT)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                character_id = character_ids[self.selected_character]
                if character_id in self.save_system.data["unlocked_characters"]:
                    self.start_game(character_id)
        elif self.scene.current == SceneManager.SHOP:
            items = self.get_shop_items()
            self.handle_vertical_menu(key, max(1, len(items)), "selected_shop")
            if key == pygame.K_ESCAPE:
                self.shop_message = ""
                self.scene.switch(SceneManager.MAIN_MENU)
            elif key in (pygame.K_RETURN, pygame.K_SPACE) and items:
                _success, message = self.buy_shop_item(items[self.selected_shop])
                self.shop_message = message
        elif self.scene.current == SceneManager.BESTIARY:
            self.handle_bestiary_key(key)
        elif self.scene.current == SceneManager.PLAYING:
            if key == pygame.K_ESCAPE:
                self.selected_pause = 0
                self.scene.switch(SceneManager.PAUSED)
            elif key == pygame.K_SPACE:
                self.player.start_dash()
            elif key == pygame.K_1:
                self.use_active_item("spinach_can")
        elif self.scene.current == SceneManager.PAUSED:
            if key in (pygame.K_a, pygame.K_LEFT, pygame.K_d, pygame.K_RIGHT):
                # 暂停菜单只有两个横向选项，所以左右键都直接切换选中项。
                self.selected_pause = 1 - self.selected_pause
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                self.confirm_pause_choice()
            elif key == pygame.K_ESCAPE:
                self.selected_pause = 0
                self.scene.switch(SceneManager.PLAYING)
        elif self.scene.current == SceneManager.UPGRADE:
            self.handle_vertical_menu(key, len(self.upgrade_options), "selected_upgrade")
            if key in (pygame.K_1, pygame.K_2, pygame.K_3):
                index = key - pygame.K_1
                if index < len(self.upgrade_options):
                    self.choose_upgrade(index)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                self.choose_upgrade(self.selected_upgrade)
        elif self.scene.current == SceneManager.RESULT:
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self.scene.switch(SceneManager.MAIN_MENU)

    def handle_bestiary_key(self, key):
        categories = self.get_bestiary_categories()
        if key == pygame.K_ESCAPE:
            self.scene.switch(SceneManager.MAIN_MENU)
        elif key in (pygame.K_a, pygame.K_LEFT):
            self.selected_bestiary_category = (self.selected_bestiary_category - 1) % len(categories)
            self.selected_bestiary_item = 0
        elif key in (pygame.K_d, pygame.K_RIGHT):
            self.selected_bestiary_category = (self.selected_bestiary_category + 1) % len(categories)
            self.selected_bestiary_item = 0
        else:
            entries = self.get_bestiary_entries(categories[self.selected_bestiary_category][0])
            self.handle_vertical_menu(key, max(1, len(entries)), "selected_bestiary_item")

    def handle_vertical_menu(self, key, count, attr):
        if count <= 0:
            return
        value = getattr(self, attr)
        if key in (pygame.K_w, pygame.K_UP):
            value = (value - 1) % count
        elif key in (pygame.K_s, pygame.K_DOWN):
            value = (value + 1) % count
        setattr(self, attr, value)

    def start_game(self, character_id):
        self.reset_run_data()
        bonus = self.save_system.get_bonus(self.shop_config)
        self.player = Player(character_id, self.characters[character_id], self.weapons_config, bonus, self.assets.get(character_id))
        self.result_saved = False
        self.win = False
        self.switch_music("explore")
        self.scene.switch(SceneManager.PLAYING)

    def update(self, dt):
        if self.scene.current != SceneManager.PLAYING:
            if self.scene.current in (
                SceneManager.MAIN_MENU,
                SceneManager.DIFFICULTY_SELECT,
                SceneManager.CHARACTER_SELECT,
                SceneManager.SHOP,
                SceneManager.BESTIARY,
                SceneManager.RESULT,
            ):
                self.switch_music("explore")
            if self.main_message_timer > 0:
                self.main_message_timer -= dt
                if self.main_message_timer <= 0:
                    self.main_message = ""
            return

        time_scale = settings.DEBUG_TIME_SCALE if settings.DEBUG_FAST_TIME else 1
        game_dt = dt * time_scale
        self.game_time += game_dt

        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, self.obstacles)

        spawned = self.spawn_system.update(game_dt, self.game_time, self.player, self.enemies, self.assets, self.obstacles)
        for enemy in spawned:
            self.register_enemy_intro(enemy.enemy_id)
            if enemy.data.get("final_boss"):
                self.final_boss = enemy
                self.play_sound("boss")
            elif enemy.is_boss:
                self.play_sound("boss")

        for enemy in list(self.enemies):
            enemy.update(dt, self.player.pos, self.obstacles)
            if enemy.can_shoot(dt, self.player.pos):
                self.enemy_projectiles.add(EnemyProjectile(
                    enemy.pos, self.player.pos, enemy.damage, enemy.data.get("bullet_speed", 260),
                    max_distance=enemy.data.get("shoot_range", 600) + 80
                ))
                self.play_sound("attack")

        self.enemy_skill_system.update(game_dt, self.game_time, self.player, self.enemies, self.enemy_attacks, self.enemy_projectiles)

        before_attacks = len(self.projectiles) + len(self.area_effects)
        for weapon in self.player.weapons:
            weapon.update(dt, self.player, self.enemies, self.projectiles, self.area_effects, self.obstacles)
        if len(self.projectiles) + len(self.area_effects) > before_attacks:
            self.play_sound("attack")

        self.projectiles.update(dt, self.obstacles)
        self.enemy_projectiles.update(dt, self.obstacles)
        self.enemy_attacks.update(dt, self.obstacles)
        self.area_effects.update(dt)
        self.update_enemy_popups(dt)
        self.update_evolution_popups(dt)
        self.collision_system.handle_projectiles(self.player, self.projectiles, self.area_effects, self.enemies, self.drops, self.obstacles)
        self.collision_system.handle_player_enemy(self.player, self.enemies, self.enemy_projectiles)
        self.collision_system.handle_enemy_attacks(self.player, self.enemy_attacks, self.obstacles)
        if self.collision_system.handle_drops(self.player, self.drops, self.active_items_config):
            self.play_sound("pickup")
            self.open_upgrade_menu()

        if self.player.is_dead():
            self.end_game(False)
        elif self.final_boss is not None and not self.final_boss.alive():
            self.end_game(True)
        else:
            self.update_dynamic_music()

    def update_dynamic_music(self):
        if any(enemy.is_boss for enemy in self.enemies):
            self.switch_music("boss")
            return
        hp_ratio = self.player.hp / self.player.max_hp
        progress = self.game_time / settings.RUN_TIME_LIMIT
        if hp_ratio <= 0.35:
            self.switch_music("danger")
        elif progress >= 0.62:
            self.switch_music("tense")
        else:
            self.switch_music("explore")

    def register_enemy_intro(self, enemy_id):
        if enemy_id in self.seen_enemy_types:
            return
        self.seen_enemy_types.add(enemy_id)
        data = self.enemies_config[enemy_id]
        self.enemy_intro_popups.append({
            "id": enemy_id,
            "name": data["name"],
            "type": data.get("type", "敌人"),
            "description": data.get("description", ""),
            "timer": 4.2,
        })

    def update_enemy_popups(self, dt):
        for popup in self.enemy_intro_popups:
            popup["timer"] -= dt
        self.enemy_intro_popups = [popup for popup in self.enemy_intro_popups if popup["timer"] > 0]

    def update_evolution_popups(self, dt):
        for popup in self.evolution_popups:
            popup["timer"] -= dt
        self.evolution_popups = [popup for popup in self.evolution_popups if popup["timer"] > 0]

    def use_active_item(self, item_id):
        if self.player.stun_timer > 0:
            return
        if self.player.use_active_item(item_id, self.active_items_config[item_id]):
            self.play_sound("pickup")

    def delete_save(self):
        self.save_system.reset_save()
        self.shop_system = ShopSystem(self.save_system, self.characters, self.weapons_config, self.shop_config)
        self.selected_character = 0
        self.selected_shop = 0
        self.main_message = "存档已删除，已恢复初始进度"
        self.main_message_timer = 2.8

    def open_upgrade_menu(self):
        self.upgrade_options = self.upgrade_system.make_options(self.player)
        self.selected_upgrade = 0
        self.scene.switch(SceneManager.UPGRADE)

    def choose_upgrade(self, index):
        if 0 <= index < len(self.upgrade_options):
            message = self.upgrade_system.apply(self.player, self.upgrade_options[index])
            if message:
                self.evolution_popups.append({"text": message, "timer": 2.8})
        self.scene.switch(SceneManager.PLAYING)

    def confirm_pause_choice(self):
        if self.selected_pause == 0:
            self.scene.switch(SceneManager.PLAYING)
        else:
            self.end_game(False)

    def end_game(self, win):
        if self.scene.current == SceneManager.RESULT or self.player is None:
            return
        self.win = win
        time_alive = min(self.game_time, settings.RUN_TIME_LIMIT)
        difficulty = self.difficulties.get(self.selected_difficulty_id, self.difficulties["hard"])
        earned = self.calculate_run_coins()
        self.save_system.add_coins(earned)
        self.save_system.update_records(time_alive, self.player.level, self.player.kill_count)
        self.last_result = {
            "win": win,
            "time": time_alive,
            "level": self.player.level,
            "kills": self.player.kill_count,
            "coins": earned,
            "difficulty": difficulty["name"],
        }
        self.result_saved = True
        self.scene.switch(SceneManager.RESULT)

    def calculate_run_coins(self):
        """返回本局最终入账金币，HUD 和结算界面共用，避免显示口径不一致。"""
        if self.player is None:
            return 0
        difficulty = self.difficulties.get(self.selected_difficulty_id, self.difficulties["hard"])
        raw_earned = self.player.coins_earned * 0.45 + self.player.kill_count // 12
        return int(raw_earned * difficulty.get("coin_bonus", 1))

    def get_shop_items(self):
        items = []
        for upgrade_id, config in self.shop_config["permanent_upgrades"].items():
            level = self.save_system.data["permanent_upgrades"][upgrade_id]
            items.append(("permanent", upgrade_id, f"{config['name']} Lv.{level}/{config['max_level']}", self.shop_system.permanent_price(upgrade_id)))
        for character_id, config in self.characters.items():
            if character_id not in self.save_system.data["unlocked_characters"]:
                items.append(("character", character_id, f"解锁角色：{config['name']}", config["price"]))
        for weapon_id, config in self.weapons_config.items():
            if weapon_id in ("blood_whip", "thousand_blades"):
                continue
            if weapon_id not in self.save_system.data["unlocked_weapons"] and config.get("price", 0) > 0:
                items.append(("weapon", weapon_id, f"解锁武器：{config['name']}", config["price"]))
        self.selected_shop = min(self.selected_shop, max(0, len(items) - 1))
        return items

    def buy_shop_item(self, item):
        kind, item_id, _title, _price = item
        if kind == "permanent":
            return self.shop_system.buy_permanent(item_id)
        if kind == "character":
            return self.shop_system.buy_character(item_id)
        return self.shop_system.buy_weapon(item_id)

    def camera_offset(self):
        return pygame.Vector2(self.player.pos.x - settings.SCREEN_WIDTH / 2, self.player.pos.y - settings.SCREEN_HEIGHT / 2)

    def world_rect(self, rect, camera):
        moved = rect.copy()
        moved.x -= round(camera.x)
        moved.y -= round(camera.y)
        return moved

    def draw(self):
        if self.scene.current == SceneManager.MAIN_MENU:
            self.draw_main_menu()
        elif self.scene.current == SceneManager.DIFFICULTY_SELECT:
            self.draw_difficulty_select()
        elif self.scene.current == SceneManager.CHARACTER_SELECT:
            self.draw_character_select()
        elif self.scene.current == SceneManager.SHOP:
            self.draw_shop()
        elif self.scene.current == SceneManager.BESTIARY:
            self.draw_bestiary()
        elif self.scene.current in (SceneManager.PLAYING, SceneManager.PAUSED, SceneManager.UPGRADE):
            self.draw_playing()
            if self.scene.current == SceneManager.PAUSED:
                self.draw_pause()
            elif self.scene.current == SceneManager.UPGRADE:
                self.draw_upgrade()
        elif self.scene.current == SceneManager.RESULT:
            self.draw_result()
        pygame.display.flip()

    def draw_text(self, text, font_key, color, center=None, topleft=None):
        surface = self.fonts[font_key].render(text, True, color)
        rect = surface.get_rect()
        if center:
            rect.center = center
        if topleft:
            rect.topleft = topleft
        self.screen.blit(surface, rect)
        return rect

    def trim_text_to_width(self, text, font_key, width):
        if self.fonts[font_key].size(text)[0] <= width:
            return text
        suffix = "..."
        trimmed = text
        while trimmed and self.fonts[font_key].size(trimmed + suffix)[0] > width:
            trimmed = trimmed[:-1]
        return trimmed + suffix if trimmed else suffix

    def draw_wrapped_text(self, text, font_key, color, x, y, width, line_gap=6, max_lines=4):
        words = list(text)
        line = ""
        lines = []
        for char in words:
            test = line + char
            if self.fonts[font_key].size(test)[0] <= width:
                line = test
            else:
                lines.append(line)
                line = char
        if line:
            lines.append(line)
        visible_lines = lines[:max_lines]
        line_height = self.fonts[font_key].get_height()
        for index, line in enumerate(visible_lines):
            self.draw_text(line, font_key, color, topleft=(x, y + index * (line_height + line_gap)))
        if not visible_lines:
            return 0
        return len(visible_lines) * line_height + (len(visible_lines) - 1) * line_gap

    def draw_button_list(self, items, selected, start_y):
        for index, text in enumerate(items):
            rect = pygame.Rect(0, start_y + index * 64, 440, 48)
            rect.centerx = settings.SCREEN_WIDTH // 2
            draw_panel(self.screen, rect, index == selected)
            self.draw_text(text, "normal", settings.WHITE, center=rect.center)

    def draw_main_menu(self):
        self.screen.fill(settings.BLACK)
        self.draw_grave_background(None)
        self.draw_text("暗夜幸存者", "big", settings.GOLD, center=(settings.SCREEN_WIDTH // 2, 110))
        self.draw_text("按WASD/方向键移动，武器自动攻击", "normal", settings.WHITE, center=(settings.SCREEN_WIDTH // 2, 180))
        self.draw_button_list(["开始游戏", "局外商店", "图鉴", "退出"], self.selected_menu, 260)
        coins = self.save_system.data["coins"]
        self.draw_text(f"金币：{coins}", "normal", settings.GOLD, center=(settings.SCREEN_WIDTH // 2, 560))
        draw_panel(self.screen, self.delete_save_rect, False)
        self.draw_text("删除存档", "small", settings.RED, center=self.delete_save_rect.center)
        if self.main_message:
            self.draw_text(self.main_message, "small", settings.GREEN, center=(settings.SCREEN_WIDTH // 2, 620))

    def draw_difficulty_select(self):
        self.screen.fill(settings.BLACK)
        self.draw_text("选择难度", "title", settings.GOLD, center=(settings.SCREEN_WIDTH // 2, 80))
        ids = list(self.difficulties.keys())
        for index, difficulty_id in enumerate(ids):
            config = self.difficulties[difficulty_id]
            rect = pygame.Rect(250, 165 + index * 125, 780, 94)
            selected = index == self.selected_difficulty
            draw_panel(self.screen, rect, selected)
            self.draw_text(config["name"], "normal", settings.WHITE, topleft=(rect.x + 24, rect.y + 16))
            detail = f"{config['description']} 敌血x{config['enemy_hp']} 敌伤x{config['enemy_damage']} 金币x{config['coin_bonus']}"
            self.draw_text(detail, "small", (205, 202, 216), topleft=(rect.x + 24, rect.y + 52))
        self.draw_text("Enter 确认，Esc 返回", "small", settings.WHITE, center=(settings.SCREEN_WIDTH // 2, 650))

    def draw_character_select(self):
        self.screen.fill(settings.BLACK)
        difficulty = self.difficulties[self.selected_difficulty_id]["name"]
        self.draw_text(f"选择角色 - {difficulty}", "title", settings.GOLD, center=(settings.SCREEN_WIDTH // 2, 80))
        ids = list(self.characters.keys())
        y = 155
        for index, character_id in enumerate(ids):
            config = self.characters[character_id]
            unlocked = character_id in self.save_system.data["unlocked_characters"]
            rect = pygame.Rect(250, y + index * 125, 780, 94)
            selected = index == self.selected_character
            draw_panel(self.screen, rect, selected)
            state = "已解锁" if unlocked else f"未解锁：{config['price']} 金币"
            self.draw_text(f"{config['name']}  -  {state}", "normal", settings.WHITE, topleft=(rect.x + 24, rect.y + 16))
            self.draw_text(config["description"], "small", (205, 202, 216), topleft=(rect.x + 24, rect.y + 52))
        self.draw_text("Enter 选择，Esc 返回难度选择", "small", settings.WHITE, center=(settings.SCREEN_WIDTH // 2, 650))

    def draw_shop(self):
        self.screen.fill(settings.BLACK)
        self.draw_text("局外商店", "title", settings.GOLD, center=(settings.SCREEN_WIDTH // 2, 52))
        self.draw_text(f"金币：{self.save_system.data['coins']}", "normal", settings.GOLD, topleft=(80, 40))
        items = self.get_shop_items()
        y = 105
        for index, item in enumerate(items):
            _kind, _id, title, price = item
            rect = pygame.Rect(170, y + index * 54, 930, 42)
            selected = index == self.selected_shop
            draw_panel(self.screen, rect, selected)
            self.draw_text(title, "small", settings.WHITE, topleft=(rect.x + 16, rect.y + 10))
            self.draw_text(f"{price} 金币", "small", settings.GOLD, topleft=(rect.right - 135, rect.y + 10))
        if self.shop_message:
            self.draw_text(self.shop_message, "normal", settings.GREEN, center=(settings.SCREEN_WIDTH // 2, 660))
        self.draw_text("Enter 购买，Esc 返回", "small", settings.WHITE, center=(settings.SCREEN_WIDTH // 2, 695))

    def get_bestiary_categories(self):
        return [("characters", "角色"), ("enemies", "敌人"), ("weapons", "武器"), ("items", "道具")]

    def get_bestiary_entries(self, category):
        if category == "characters":
            return [(key, value["name"], value) for key, value in self.characters.items()]
        if category == "enemies":
            return [(key, value["name"], value) for key, value in self.enemies_config.items()]
        if category == "weapons":
            return [(key, value["name"], value) for key, value in self.weapons_config.items()]
        entries = [(key, value["name"], value) for key, value in self.passives_config.items()]
        entries.extend([(key, value["name"], value) for key, value in self.active_items_config.items()])
        return entries

    def draw_bestiary(self):
        self.screen.fill(settings.BLACK)
        self.draw_text("图鉴", "title", settings.GOLD, center=(settings.SCREEN_WIDTH // 2, 48))
        categories = self.get_bestiary_categories()
        for index, (_category_id, name) in enumerate(categories):
            rect = pygame.Rect(150 + index * 245, 92, 210, 42)
            draw_panel(self.screen, rect, index == self.selected_bestiary_category)
            self.draw_text(name, "normal", settings.WHITE, center=rect.center)

        category_id = categories[self.selected_bestiary_category][0]
        entries = self.get_bestiary_entries(category_id)
        self.selected_bestiary_item = min(self.selected_bestiary_item, max(0, len(entries) - 1))
        for index, (_entry_id, name, _data) in enumerate(entries[:12]):
            rect = pygame.Rect(80, 160 + index * 42, 310, 34)
            draw_panel(self.screen, rect, index == self.selected_bestiary_item)
            self.draw_text(name, "small", settings.WHITE, topleft=(rect.x + 14, rect.y + 7))

        if entries:
            entry_id, name, data = entries[self.selected_bestiary_item]
            rect = pygame.Rect(430, 160, 760, 470)
            draw_panel(self.screen, rect, False)
            icon = self.assets.get(entry_id)
            if icon:
                self.screen.blit(pygame.transform.scale(icon, (74, 74)), (rect.x + 24, rect.y + 24))
            self.draw_text(name, "title", settings.GOLD, topleft=(rect.x + 120, rect.y + 24))
            lines = self.make_bestiary_lines(category_id, entry_id, data)
            y = rect.y + 92
            for line in lines:
                if line:
                    text_height = self.draw_wrapped_text(line, "small", settings.WHITE, rect.x + 28, y, rect.width - 56, max_lines=3)
                    y += text_height + 18
        self.draw_text("←/→ 切换分类，↑/↓ 选择，Esc 返回", "small", settings.WHITE, center=(settings.SCREEN_WIDTH // 2, 680))

    def make_bestiary_lines(self, category, entry_id, data):
        if category == "characters":
            return [
                f"类型：可玩角色",
                f"说明：{data['description']}",
                f"生命：{data['max_hp']}  移速：{data['speed']}  初始武器：{self.weapons_config[data['start_weapon']]['name']}",
            ]
        if category == "enemies":
            attack = self.describe_enemy_attack(data)
            return [
                f"类型：{data.get('type', '敌人')}  攻击方式：{attack}",
                f"说明：{data.get('description', '')}",
                f"生命：{data['hp']}  伤害：{data['damage']}  移速：{data['speed']}  经验：{data['exp']}",
            ]
        if category == "weapons":
            evolve = "无"
            if data.get("evolve_with"):
                evolve = f"{data['name']} Lv.8 + {self.passives_config[data['evolve_with']]['name']} = {self.weapons_config[data['evolves_to']]['name']}"
            range_text = data.get("range", "-")
            target_range_text = data.get("target_range", "-")
            return [
                f"类型：{data['kind']}  CD：{data.get('cooldown', '-')}秒  伤害：{data.get('damage', '-')}",
                f"范围：{range_text}  锁敌射程：{target_range_text}",
                f"说明：{data.get('description', '')}",
                f"进化规则：{evolve}",
            ]
        item_type = data.get("type", "被动道具")
        funny = data.get("funny", "据说这个东西很强，但策划还没想好怎么解释。")
        return [
            f"类型：{item_type}",
            f"说明：{data.get('description', '')}",
            f"介绍：{funny}",
        ]

    def describe_enemy_attack(self, data):
        names = {
            "charge": "蓄力冲撞",
            "stomp": "震地眩晕",
            "blink": "闪现伏击",
            "bone_spread": "骨刺",
            "laser": "激光",
            "shield_charge": "盾冲眩晕",
            "chains": "锁链眩晕",
            "big_explosion": "范围爆炸",
            "ring_shots": "环形弹幕",
        }
        attacks = ["远程弹" if data.get("ranged") else "接触伤害"]
        attacks.extend(names.get(skill, skill) for skill in data.get("skills", []))
        return "、".join(attacks)

    def draw_playing(self):
        self.screen.fill(settings.BLACK)
        camera = self.camera_offset()
        self.draw_grave_background(camera)

        for group in (self.obstacles, self.drops, self.enemy_attacks, self.area_effects, self.projectiles, self.enemy_projectiles, self.enemies):
            for sprite in group:
                image = sprite.image
                if getattr(sprite, "hit_flash_timer", 0) > 0:
                    image = image.copy()
                    image.fill((255, 135, 135, 255), special_flags=pygame.BLEND_RGBA_MULT)
                self.screen.blit(image, self.world_rect(sprite.rect, camera))
        self.draw_player(camera)
        self.draw_hud()
        self.draw_boss_bars()
        self.draw_enemy_intros()
        self.draw_evolution_popups()
        self.draw_collision_debug(camera)

    def draw_player(self, camera):
        rect = self.world_rect(self.player.rect, camera)
        image = self.player.image
        if self.player.hit_flash_timer > 0:
            image = image.copy()
            image.fill((255, 135, 135, 255), special_flags=pygame.BLEND_RGBA_MULT)
        if self.player.spinach_timer > 0:
            ratio = self.player.spinach_ratio()
            scale = 1.18 + 0.12 * ratio
            size = (int(image.get_width() * scale), int(image.get_height() * scale))
            image = pygame.transform.scale(image, size)
            image_rect = image.get_rect(center=rect.center)
            pygame.draw.circle(self.screen, (70, 220, 96, 85), rect.center, max(size) // 2 + 8)
            self.screen.blit(image, image_rect)
            return
        self.screen.blit(image, rect)
        if self.player.stun_timer > 0:
            radius = int(30 + 5 * abs((self.player.stun_timer * 8) % 2 - 1))
            pygame.draw.circle(self.screen, settings.GOLD, rect.center, radius, 3)

    def draw_collision_debug(self, camera):
        if not settings.DEBUG_DRAW_COLLISION:
            return
        for obstacle in self.obstacles:
            pygame.draw.rect(self.screen, (80, 220, 120), self.world_rect(obstacle.collision_rect, camera), 2)
        pygame.draw.rect(self.screen, (80, 170, 255), self.world_rect(self.player.collision_rect, camera), 2)
        for enemy in self.enemies:
            pygame.draw.rect(self.screen, (255, 90, 90), self.world_rect(enemy.rect, camera), 2)

    def draw_grave_background(self, camera):
        if camera is None:
            camera = pygame.Vector2(0, 0)
        tile = settings.TILE_SIZE
        start_x = -int(camera.x) % tile - tile
        start_y = -int(camera.y) % tile - tile
        for x in range(start_x, settings.SCREEN_WIDTH + tile, tile):
            for y in range(start_y, settings.SCREEN_HEIGHT + tile, tile):
                shade = 20 + ((x // tile + y // tile) % 2) * 6
                rect = pygame.Rect(x, y, tile, tile)
                if self.assets.get("cemetery_tile"):
                    self.screen.blit(self.assets["cemetery_tile"], rect)
                else:
                    pygame.draw.rect(self.screen, (shade, shade + 8, shade + 7), rect)
                    pygame.draw.rect(self.screen, (32, 40, 39), rect, 1)

    def draw_hud(self):
        hp_ratio = max(0, self.player.hp / self.player.max_hp)
        draw_bar(self.screen, pygame.Rect(22, 18, 310, 28), hp_ratio, settings.RED)
        self.draw_text(f"HP {int(self.player.hp)}/{self.player.max_hp}", "small", settings.WHITE, topleft=(34, 23))

        exp_ratio = self.player.exp / self.player.next_exp
        draw_bar(self.screen, pygame.Rect(22, 54, 310, 18), exp_ratio, settings.BLUE)

        time_text = self.format_time(self.game_time)
        difficulty = self.difficulties[self.selected_difficulty_id]["name"]
        run_coins = self.calculate_run_coins()
        self.draw_text(time_text, "title", settings.WHITE, center=(settings.SCREEN_WIDTH // 2, 35))
        self.draw_text(f"难度：{difficulty}  Lv.{self.player.level}  击杀 {self.player.kill_count}  金币 {run_coins}", "small", settings.WHITE, topleft=(22, 82))

        status_y = 112
        if self.player.dash_cooldown > 0:
            self.draw_text(f"冲刺冷却 {self.player.dash_cooldown:.1f}s", "small", settings.GOLD, topleft=(22, status_y))
            status_y += 26
        else:
            self.draw_text("Space 冲刺：就绪", "small", settings.GREEN, topleft=(22, status_y))
            status_y += 26
        if self.player.stun_timer > 0:
            self.draw_text(f"眩晕中 {self.player.stun_timer:.1f}s", "small", settings.GOLD, topleft=(22, status_y))
            status_y += 26
        if self.player.spinach_timer > 0:
            self.draw_text(f"菠菜强化 {self.player.spinach_timer:.1f}s", "small", settings.GREEN, topleft=(22, status_y))
        self.draw_weapon_list()
        self.draw_active_items()

    def draw_weapon_list(self):
        names = [f"{weapon.name}Lv.{weapon.level}" for weapon in self.player.weapons]
        lines = []
        line = ""
        max_width = 460
        for name in names:
            test = name if not line else f"{line}  {name}"
            if self.fonts["small"].size(test)[0] <= max_width:
                line = test
            else:
                lines.append(line)
                line = name
        if line:
            lines.append(line)
        hidden = max(0, len(lines) - 3)
        lines = lines[:3]
        if hidden:
            lines[-1] = f"{lines[-1]}  等{hidden}行"
        start_y = settings.SCREEN_HEIGHT - 132 - (len(lines) - 1) * 22
        for index, line in enumerate(lines):
            self.draw_text(line, "small", (220, 216, 230), topleft=(22, start_y + index * 22))

    def draw_active_items(self):
        x, y = 22, settings.SCREEN_HEIGHT - 98
        for item_id, count in self.player.active_items.items():
            if count <= 0:
                continue
            config = self.active_items_config[item_id]
            rect = pygame.Rect(x, y, 180, 46)
            draw_panel(self.screen, rect, False)
            icon = self.assets.get(item_id)
            if icon:
                self.screen.blit(pygame.transform.scale(icon, (32, 32)), (x + 8, y + 7))
            self.draw_text(f"{config['use_key']}键 {config['name']} x{count}", "small", settings.WHITE, topleft=(x + 48, y + 13))
            y -= 52

    def draw_boss_bars(self):
        bosses = [enemy for enemy in self.enemies if enemy.is_boss]
        for index, boss in enumerate(bosses[:4]):
            rect = pygame.Rect(settings.SCREEN_WIDTH // 2 - 260, 76 + index * 34, 520, 22)
            draw_bar(self.screen, rect, max(0, boss.hp / boss.max_hp), settings.RED, settings.GOLD)
            self.draw_text(f"{boss.name}  {max(0, int(boss.hp))}/{boss.max_hp}", "small", settings.WHITE, center=rect.center)

    def draw_enemy_intros(self):
        for index, popup in enumerate(self.enemy_intro_popups[:3]):
            rect = pygame.Rect(settings.SCREEN_WIDTH - 390, 24 + index * 116, 360, 96)
            draw_panel(self.screen, rect, False)
            icon = self.assets.get(popup["id"])
            if icon:
                self.screen.blit(pygame.transform.scale(icon, (48, 48)), (rect.x + 14, rect.y + 20))
            text_x = rect.x + 74
            self.draw_text(f"新敌人：{popup['name']} ({popup['type']})", "small", settings.GOLD, topleft=(text_x, rect.y + 12))
            self.draw_wrapped_text(popup["description"], "small", settings.WHITE, text_x, rect.y + 42, rect.width - 88, max_lines=2)

    def draw_evolution_popups(self):
        for index, popup in enumerate(self.evolution_popups[:2]):
            rect = pygame.Rect(settings.SCREEN_WIDTH // 2 - 230, 112 + index * 58, 460, 44)
            draw_panel(self.screen, rect, True)
            self.draw_text(popup["text"], "normal", settings.GOLD, center=rect.center)

    def draw_pause(self):
        self.draw_overlay()
        self.draw_text("暂停", "big", settings.GOLD, center=(settings.SCREEN_WIDTH // 2, 280))
        self.draw_text("←/→ 切换，Enter 确认", "normal", settings.WHITE, center=(settings.SCREEN_WIDTH // 2, 350))
        for index, (text, rect) in enumerate(self.pause_buttons):
            draw_panel(self.screen, rect, index == self.selected_pause)
            color = settings.GREEN if index == 0 else settings.RED
            self.draw_text(text, "normal", color, center=rect.center)

    def draw_upgrade(self):
        self.draw_overlay()
        self.draw_text("选择强化", "title", settings.GOLD, center=(settings.SCREEN_WIDTH // 2, 120))
        for index, option in enumerate(self.upgrade_options):
            rect = pygame.Rect(260, 205 + index * 115, 760, 82)
            draw_panel(self.screen, rect, index == self.selected_upgrade)
            self.draw_text(f"{index + 1}. {option['title']}", "normal", settings.WHITE, topleft=(rect.x + 22, rect.y + 12))
            description = self.trim_text_to_width(option["description"], "small", rect.width - 44)
            self.draw_text(description, "small", (210, 207, 220), topleft=(rect.x + 22, rect.y + 48))

    def draw_result(self):
        self.screen.fill(settings.BLACK)
        title = "通关成功" if self.last_result.get("win") else "战斗结束"
        self.draw_text(title, "big", settings.GOLD if self.last_result.get("win") else settings.RED, center=(settings.SCREEN_WIDTH // 2, 120))
        lines = [
            f"难度：{self.last_result.get('difficulty', '困难')}",
            f"存活时间：{self.format_time(self.last_result.get('time', 0))}",
            f"最高等级：{self.last_result.get('level', 1)}",
            f"击杀数量：{self.last_result.get('kills', 0)}",
            f"获得金币：{self.last_result.get('coins', 0)}",
            f"当前金币：{self.save_system.data['coins']}",
        ]
        for index, line in enumerate(lines):
            self.draw_text(line, "normal", settings.WHITE, center=(settings.SCREEN_WIDTH // 2, 210 + index * 44))
        self.draw_text("Enter 返回主菜单", "normal", settings.GOLD, center=(settings.SCREEN_WIDTH // 2, 570))

    def draw_overlay(self):
        overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        self.screen.blit(overlay, (0, 0))

    def format_time(self, seconds):
        seconds = max(0, int(seconds))
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

