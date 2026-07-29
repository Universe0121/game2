class ShopSystem:
    def __init__(self, save_system, characters, weapons, shop_config):
        self.save_system = save_system
        self.characters = characters
        self.weapons = weapons
        self.shop_config = shop_config

    def permanent_price(self, upgrade_id):
        config = self.shop_config["permanent_upgrades"][upgrade_id]
        level = self.save_system.data["permanent_upgrades"][upgrade_id]
        return int(config["base_price"] * (config["price_growth"] ** level))

    def buy_permanent(self, upgrade_id):
        config = self.shop_config["permanent_upgrades"][upgrade_id]
        level = self.save_system.data["permanent_upgrades"][upgrade_id]
        if level >= config["max_level"]:
            return False, "已经满级"
        price = self.permanent_price(upgrade_id)
        if not self.save_system.spend_coins(price):
            return False, "金币不足"
        self.save_system.upgrade_permanent(upgrade_id)
        return True, "购买成功"

    def buy_character(self, character_id):
        if character_id in self.save_system.data["unlocked_characters"]:
            return False, "已经解锁"
        price = self.characters[character_id]["price"]
        if not self.save_system.spend_coins(price):
            return False, "金币不足"
        self.save_system.unlock_character(character_id)
        return True, "角色已解锁"

    def buy_weapon(self, weapon_id):
        if weapon_id in self.save_system.data["unlocked_weapons"]:
            return False, "已经解锁"
        price = self.weapons[weapon_id].get("price", 0)
        if price <= 0:
            return False, "无需购买"
        if not self.save_system.spend_coins(price):
            return False, "金币不足"
        self.save_system.unlock_weapon(weapon_id)
        return True, "武器已解锁"
