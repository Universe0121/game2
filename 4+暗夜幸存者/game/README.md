# 暗夜幸存者

一个用 Python + Pygame 制作的类《吸血鬼幸存者》课程项目原型。

## 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 启动

macOS / Linux：

```bash
source .venv/bin/activate
python main.py
```

Windows 源码运行：

```powershell
.venv\Scripts\activate
python main.py
```

Windows 也可以运行打包后的文件：

```powershell
dist\暗夜幸存者.exe
```

## 操作

- WASD / 方向键：移动或菜单选择
- Enter / Space：确认
- Esc：返回或暂停
- 1 / 2 / 3：升级界面快速选择
- 战斗中 1：使用菠菜罐头
- 战斗中 Space：冲刺，短暂无敌，可躲避眩晕技能
- 暂停界面 ←/→：切换“继续/结束”，Enter 确认

## 代码结构说明

- `core/game.py`：主循环、场景切换、HUD 和界面绘制
- `game_objects/player.py`：玩家属性、移动、冲刺、眩晕、武器和道具状态
- `game_objects/enemy_attack.py`：敌人技能的预警区和伤害区
- `systems/enemy_skill_system.py`：敌人特殊技能释放逻辑
- `systems/spawn_system.py`：刷怪节奏、精英怪概率、敌人随等级成长和安全出生点选择
- `systems/collision_system.py`：玩家、敌人、子弹、掉落物、敌方技能碰撞

## 调试选项

编辑 `config/settings.py`：

```python
# 加速游戏时间，方便测试 Boss 和结算流程
DEBUG_FAST_TIME = True

# 显示障碍物、玩家和敌人的碰撞框
DEBUG_DRAW_COLLISION = True
```

调试完成后建议将这两个选项恢复为 `False`。

## 存档说明

源码运行时存档位于项目根目录的 `save_data.json`，打包运行时存档位于可执行文件所在目录。

保存时会先写入同目录临时文件，再替换为 `save_data.json`，避免程序中断留下半截 JSON。

## 打包参考

```powershell
pyinstaller --onefile --windowed --name "暗夜幸存者" --icon "resources/images/app_icon.ico" --add-data "config;config" --add-data "resources;resources" main.py
```
