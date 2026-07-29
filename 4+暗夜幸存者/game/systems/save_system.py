import json
import os
import tempfile
from copy import deepcopy

from config import settings


DEFAULT_SAVE = {
    "coins": 0,
    "unlocked_characters": ["hunter"],
    "unlocked_weapons": ["whip", "knife", "magic_bolt"],
    "permanent_upgrades": {"max_hp": 0, "speed": 0, "damage": 0, "pickup": 0},
    "records": {"best_time": 0, "best_level": 1, "best_kills": 0}
}


class SaveSystem:
    def __init__(self, path=None):
        self.path = path or settings.SAVE_FILE
        self.data = self.load()

    def load(self):
        loaded = None
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as file:
                    loaded = json.load(file)
            except (json.JSONDecodeError, OSError):
                loaded = None
        if not isinstance(loaded, dict):
            return deepcopy(DEFAULT_SAVE)

        data = deepcopy(DEFAULT_SAVE)
        data.update(loaded)
        data["permanent_upgrades"] = DEFAULT_SAVE["permanent_upgrades"].copy() | data.get("permanent_upgrades", {})
        data["records"] = DEFAULT_SAVE["records"].copy() | data.get("records", {})
        return data

    def save(self):
        directory = os.path.dirname(self.path) or "."
        os.makedirs(directory, exist_ok=True)
        temp_path = None
        try:
            # 先写同目录临时文件，再原子替换，避免程序中断留下半截 JSON。
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=directory,
                prefix=".save_data_",
                suffix=".tmp",
                delete=False,
            ) as file:
                temp_path = file.name
                json.dump(self.data, file, ensure_ascii=False, indent=2)
                file.flush()
                os.fsync(file.fileno())

            os.replace(temp_path, self.path)
        except OSError:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            raise

    def reset_save(self):
        """删除玩家进度，恢复到新存档状态。"""
        self.data = deepcopy(DEFAULT_SAVE)
        self.save()

    def add_coins(self, amount):
        self.data["coins"] += int(amount)
        self.save()

    def spend_coins(self, amount):
        if self.data["coins"] < amount:
            return False
        self.data["coins"] -= amount
        self.save()
        return True

    def unlock_character(self, character_id):
        if character_id not in self.data["unlocked_characters"]:
            self.data["unlocked_characters"].append(character_id)
            self.save()

    def unlock_weapon(self, weapon_id):
        if weapon_id not in self.data["unlocked_weapons"]:
            self.data["unlocked_weapons"].append(weapon_id)
            self.save()

    def upgrade_permanent(self, upgrade_id):
        self.data["permanent_upgrades"][upgrade_id] += 1
        self.save()

    def update_records(self, time_alive, level, kills):
        records = self.data["records"]
        records["best_time"] = max(records.get("best_time", 0), int(time_alive))
        records["best_level"] = max(records.get("best_level", 1), level)
        records["best_kills"] = max(records.get("best_kills", 0), kills)
        self.save()

    def get_bonus(self, shop_config):
        upgrades = self.data["permanent_upgrades"]
        return {
            "max_hp": upgrades["max_hp"] * shop_config["permanent_upgrades"]["max_hp"]["value"],
            "speed": upgrades["speed"] * shop_config["permanent_upgrades"]["speed"]["value"],
            "damage": upgrades["damage"] * shop_config["permanent_upgrades"]["damage"]["value"],
            "pickup": upgrades["pickup"] * shop_config["permanent_upgrades"]["pickup"]["value"],
        }
