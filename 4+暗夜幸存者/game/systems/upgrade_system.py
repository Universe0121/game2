import random


PASSIVE_UPGRADE_DESCRIPTIONS = {
    "hollow_sword": "全武器伤害提高，可进化血鞭。",
    "armor": "减少受到的伤害，提高容错。",
    "focus_crystal": "提高武器伤害，清怪更快。",
    "clover": "扩大拾取范围，提高幸运，可进化千刃。",
}


class UpgradeSystem:
    def __init__(self, weapon_config, passive_config, save_system):
        self.weapon_config = weapon_config
        self.passive_config = passive_config
        self.save_system = save_system

    def make_options(self, player):
        options = []

        for weapon in player.weapons:
            if weapon.level < weapon.config["max_level"]:
                options.append({
                    "type": "weapon",
                    "id": weapon.weapon_id,
                    "title": f"升级 {weapon.name}",
                    "description": f"提升到 Lv.{weapon.level + 1}，增强伤害、范围或数量。"
                })

        owned_weapon_ids = {weapon.weapon_id for weapon in player.weapons}
        for weapon_id, config in self.weapon_config.items():
            if weapon_id in ("blood_whip", "thousand_blades"):
                continue
            if weapon_id in owned_weapon_ids:
                continue
            if weapon_id not in self.save_system.data["unlocked_weapons"]:
                continue
            options.append({
                "type": "new_weapon",
                "id": weapon_id,
                "title": f"获得 {config['name']}",
                "description": config["description"]
            })

        for passive_id, config in self.passive_config.items():
            level = player.passives.get(passive_id, 0)
            if level < config["max_level"]:
                title = f"获得 {config['name']}" if level == 0 else f"升级 {config['name']}"
                options.append({
                    "type": "passive",
                    "id": passive_id,
                    "title": title,
                    "description": self.passive_upgrade_description(passive_id, level)
                })

        options.extend([
            {"type": "stat", "id": "heal", "title": "紧急治疗", "description": "立即恢复 30 点生命。"},
            {"type": "stat", "id": "speed", "title": "轻盈步伐", "description": "本局移动速度 +12。"},
            {"type": "stat", "id": "pickup", "title": "灵魂磁石", "description": "本局拾取范围 +18。"}
        ])

        random.shuffle(options)
        return options[:3]

    def passive_upgrade_description(self, passive_id, level):
        # 图鉴里保留详细说明，战斗升级卡片使用短说明，避免文字超出面板。
        text = PASSIVE_UPGRADE_DESCRIPTIONS.get(passive_id, "提升本局被动能力。")
        return f"{text} 当前 Lv.{level}"

    def apply(self, player, option):
        option_type = option["type"]
        option_id = option["id"]
        if option_type in ("weapon", "new_weapon"):
            player.add_or_upgrade_weapon(option_id, self.weapon_config[option_id])
        elif option_type == "passive":
            player.add_or_upgrade_passive(option_id, self.passive_config[option_id])
        elif option_id == "heal":
            player.heal(30)
        elif option_id == "speed":
            player.speed += 12
        elif option_id == "pickup":
            player.pickup_range += 18
        return self.try_evolve(player)

    def try_evolve(self, player):
        for weapon in list(player.weapons):
            config = weapon.config
            passive_id = config.get("evolve_with")
            new_id = config.get("evolves_to")
            if not passive_id or not new_id:
                continue
            if weapon.level >= config["max_level"] and player.passives.get(passive_id, 0) > 0:
                return player.evolve_weapon(weapon.weapon_id, new_id, self.weapon_config[new_id])
        return ""
