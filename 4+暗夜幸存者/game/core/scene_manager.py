class SceneManager:
    """简单状态机，避免在主循环里到处写字符串判断。"""

    MAIN_MENU = "main_menu"
    DIFFICULTY_SELECT = "difficulty_select"
    CHARACTER_SELECT = "character_select"
    SHOP = "shop"
    BESTIARY = "bestiary"
    PLAYING = "playing"
    PAUSED = "paused"
    UPGRADE = "upgrade"
    RESULT = "result"

    def __init__(self):
        self.current = self.MAIN_MENU
        self.previous = None

    def switch(self, scene):
        self.previous = self.current
        self.current = scene
