# 外部素材来源

本项目优先使用 CC0 / Public Domain 像素素材，方便课程展示和后续二次修改。

- 1-Bit Graveyard Pixel Art Asset Pack，作者 Fava Beans，OpenGameArt，CC0：https://opengameart.org/content/1-bit-graveyard-pixel-art-asset-pack
- RPG Character 'Vampire'，作者 Chasersgaming，OpenGameArt，CC0：https://opengameart.org/content/rpg-character-vampire
- Tileset: Cemetery (16x16)，作者 mutantleg，OpenGameArt，CC0：https://opengameart.org/content/tileset-cemetery-16x16
- Zombie RPG sprites，作者 Curt，Liberated Pixel Cup / OpenGameArt，CC0：https://lpc.opengameart.org/content/zombie-rpg-sprites

说明：游戏代码保留 Pygame 绘制的兜底素材。若外部素材下载失败或后续替换素材，只要把对应 PNG 放在 `resources/images/` 下并使用配置约定的文件名即可。

当前版本的主用角色、敌人、武器、道具和攻击特效素材由 `tools/generate_project_assets.py` 生成，用于保证同一尺寸和同一暗黑像素风风格。外部素材主要作为参考和可替换资源。
