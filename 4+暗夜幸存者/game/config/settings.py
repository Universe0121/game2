import os
import sys


# 屏幕与帧率
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
GAME_TITLE = "暗夜幸存者"

# 单局时长：20 分钟，单位为秒
RUN_TIME_LIMIT = 20 * 60
MID_BOSS_TIME = 12 * 60
FINAL_BOSS_TIME = 20 * 60

# 调试时可以改成 True，让时间流速变快。
DEBUG_FAST_TIME = False
DEBUG_TIME_SCALE = 6.0
DEBUG_DRAW_COLLISION = False

# 游戏世界
TILE_SIZE = 64
SPAWN_PADDING = 120
MAX_ENEMIES = 260
PLAYER_HIT_COOLDOWN = 0.8

# 文件路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if getattr(sys, "frozen", False):
    SAVE_DIR = os.path.dirname(sys.executable)
else:
    SAVE_DIR = BASE_DIR
SAVE_FILE = os.path.join(SAVE_DIR, "save_data.json")
IMAGE_DIR = os.path.join(BASE_DIR, "resources", "images")

# 常用颜色
BLACK = (10, 10, 16)
WHITE = (240, 235, 220)
RED = (210, 64, 72)
GREEN = (94, 201, 116)
BLUE = (87, 158, 224)
GOLD = (236, 186, 76)
PURPLE = (132, 92, 190)
DARK_PURPLE = (34, 25, 46)
GRAY = (86, 88, 101)
PANEL = (26, 24, 34)
PANEL_LIGHT = (45, 42, 58)
