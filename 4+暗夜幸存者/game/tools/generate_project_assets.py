import math
import os
import struct
import wave

import pygame


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE_DIR = os.path.join(ROOT, "resources", "images")
AUDIO_DIR = os.path.join(ROOT, "resources", "audio")


def pixel_surface(size=64):
    return pygame.Surface((size, size), pygame.SRCALPHA)


def save(surface, name):
    pygame.image.save(surface, os.path.join(IMAGE_DIR, f"{name}.png"))


def draw_shadow(surface):
    pygame.draw.ellipse(surface, (0, 0, 0, 80), (13, 45, 38, 10))


def make_hero(name, coat, face, accent):
    s = pixel_surface()
    draw_shadow(s)
    pygame.draw.rect(s, coat, (25, 24, 14, 24))
    pygame.draw.rect(s, coat, (20, 30, 24, 8))
    pygame.draw.rect(s, face, (24, 12, 16, 14))
    pygame.draw.rect(s, accent, (22, 8, 20, 5))
    pygame.draw.rect(s, (18, 15, 24), (26, 17, 3, 3))
    pygame.draw.rect(s, (18, 15, 24), (35, 17, 3, 3))
    pygame.draw.rect(s, accent, (19, 25, 7, 21))
    pygame.draw.rect(s, accent, (38, 25, 7, 21))
    pygame.draw.rect(s, (38, 31, 42), (24, 48, 6, 8))
    pygame.draw.rect(s, (38, 31, 42), (34, 48, 6, 8))
    save(s, name)


def make_enemy(name, body, detail, boss=False, ranged=False):
    s = pixel_surface()
    draw_shadow(s)
    if boss:
        pygame.draw.rect(s, body, (18, 14, 28, 36))
        pygame.draw.rect(s, detail, (15, 10, 34, 8))
        pygame.draw.rect(s, (230, 218, 170), (22, 22, 6, 5))
        pygame.draw.rect(s, (230, 218, 170), (36, 22, 6, 5))
        pygame.draw.rect(s, detail, (13, 24, 9, 22))
        pygame.draw.rect(s, detail, (42, 24, 9, 22))
    else:
        pygame.draw.rect(s, body, (21, 20, 22, 26))
        pygame.draw.rect(s, detail, (23, 13, 18, 11))
        pygame.draw.rect(s, (16, 13, 20), (26, 19, 3, 3))
        pygame.draw.rect(s, (16, 13, 20), (35, 19, 3, 3))
        pygame.draw.rect(s, body, (15, 25, 9, 14))
        pygame.draw.rect(s, body, (40, 25, 9, 14))
        if ranged:
            pygame.draw.rect(s, (104, 72, 190), (45, 18, 5, 24))
            pygame.draw.circle(s, (201, 178, 255), (48, 15), 5)
    save(s, name)


def make_icon(name, colors):
    s = pixel_surface()
    pygame.draw.rect(s, (22, 19, 28), (8, 8, 48, 48), border_radius=6)
    pygame.draw.rect(s, colors[0], (12, 12, 40, 40), 2, border_radius=5)
    pygame.draw.line(s, colors[1], (20, 44), (44, 20), 5)
    pygame.draw.circle(s, colors[2], (42, 22), 7)
    save(s, name)


def make_spinach():
    s = pixel_surface()
    draw_shadow(s)
    pygame.draw.rect(s, (35, 119, 68), (21, 10, 22, 42), border_radius=5)
    pygame.draw.rect(s, (212, 232, 178), (24, 21, 16, 12))
    pygame.draw.arc(s, (20, 75, 42), (25, 27, 15, 16), 0.4, 4.2, 4)
    pygame.draw.rect(s, (232, 237, 206), (23, 7, 18, 5))
    save(s, "spinach_can")


def make_passive_icon(name, kind):
    s = pixel_surface()
    pygame.draw.rect(s, (22, 19, 28), (8, 8, 48, 48), border_radius=6)
    pygame.draw.rect(s, (176, 154, 95), (12, 12, 40, 40), 2, border_radius=5)
    if kind == "sword":
        pygame.draw.line(s, (226, 232, 238), (20, 45), (43, 18), 6)
        pygame.draw.line(s, (90, 96, 112), (20, 45), (43, 18), 2)
        pygame.draw.rect(s, (160, 104, 60), (16, 42, 13, 5))
    elif kind == "armor":
        pygame.draw.polygon(s, (118, 128, 146), [(32, 13), (47, 20), (43, 43), (32, 52), (21, 43), (17, 20)])
        pygame.draw.line(s, (220, 225, 232), (32, 18), (32, 48), 2)
        pygame.draw.rect(s, (68, 72, 86), (24, 23, 16, 6))
    elif kind == "crystal":
        pygame.draw.polygon(s, (104, 196, 236), [(32, 10), (47, 27), (41, 51), (23, 51), (17, 27)])
        pygame.draw.polygon(s, (218, 248, 255), [(32, 15), (40, 28), (32, 45), (24, 28)], 2)
    elif kind == "clover":
        for cx, cy in [(27, 26), (37, 26), (27, 36), (37, 36)]:
            pygame.draw.circle(s, (77, 185, 95), (cx, cy), 8)
        pygame.draw.line(s, (45, 119, 60), (34, 39), (41, 51), 3)
    save(s, name)


def make_background_tile():
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    s.fill((24, 30, 31))
    for x in range(0, 128, 16):
        for y in range(0, 128, 16):
            shade = 22 + ((x // 16 + y // 16) % 3) * 4
            pygame.draw.rect(s, (shade, shade + 8, shade + 7), (x, y, 16, 16))
            pygame.draw.rect(s, (32, 40, 39), (x, y, 16, 16), 1)
    for rect in [(12, 18, 12, 18), (78, 20, 18, 12), (40, 76, 16, 22), (94, 86, 20, 16)]:
        pygame.draw.rect(s, (48, 55, 58), rect, border_radius=3)
        pygame.draw.line(s, (80, 83, 92), (rect[0] + 3, rect[1] + 4), (rect[0] + rect[2] - 3, rect[1] + 4), 2)
    for pos in [(28, 54), (66, 58), (106, 38), (21, 103), (71, 111)]:
        pygame.draw.rect(s, (35, 54, 42), (pos[0], pos[1], 10, 4))
        pygame.draw.rect(s, (41, 67, 48), (pos[0] + 3, pos[1] - 5, 4, 9))
    pygame.image.save(s, os.path.join(IMAGE_DIR, "cemetery_ground.png"))


def make_effect(name, color):
    s = pixel_surface()
    for radius, alpha in [(28, 60), (20, 110), (11, 210)]:
        pygame.draw.circle(s, (*color, alpha), (32, 32), radius)
    pygame.draw.line(s, (*color, 240), (10, 34), (54, 30), 4)
    save(s, name)


def tone(freq, duration, volume=0.35, rate=44100):
    samples = []
    total = int(duration * rate)
    for i in range(total):
        t = i / rate
        env = max(0, 1 - i / total)
        value = int(math.sin(2 * math.pi * freq * t) * 32767 * volume * env)
        samples.append(struct.pack("<hh", value, value))
    return b"".join(samples)


def write_wav(path, chunks, rate=44100):
    with wave.open(path, "wb") as file:
        file.setnchannels(2)
        file.setsampwidth(2)
        file.setframerate(rate)
        file.writeframes(b"".join(chunks))


def make_audio():
    write_wav(os.path.join(AUDIO_DIR, "attack.wav"), [tone(520, 0.07), tone(270, 0.05)])
    write_wav(os.path.join(AUDIO_DIR, "pickup.wav"), [tone(760, 0.05), tone(980, 0.08)])
    write_wav(os.path.join(AUDIO_DIR, "boss.wav"), [tone(120, 0.25, 0.45), tone(80, 0.25, 0.35)])
    tracks = {
        "bgm_explore.wav": ([147, 147, 175, 196, 175, 147, 131, 147], 0.10),
        "bgm_tense.wav": ([196, 220, 196, 247, 220, 196, 175, 196], 0.13),
        "bgm_danger.wav": ([110, 147, 110, 165, 147, 110, 98, 110], 0.15),
        "bgm_boss.wav": ([82, 98, 123, 98, 82, 73, 82, 110], 0.18),
    }
    for filename, (notes, volume) in tracks.items():
        melody = []
        for _ in range(12):
            for note in notes:
                melody.append(tone(note, 0.15, volume))
                melody.append(tone(note / 2, 0.15, volume * 0.72))
        write_wav(os.path.join(AUDIO_DIR, filename), melody)


def main():
    os.makedirs(IMAGE_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)
    pygame.init()
    make_background_tile()
    make_hero("hunter", (93, 42, 57), (226, 194, 158), (214, 180, 74))
    make_hero("mage", (48, 66, 138), (222, 190, 168), (104, 177, 238))
    make_hero("knight", (82, 84, 91), (214, 185, 150), (188, 190, 206))
    make_enemy("bat", (77, 55, 128), (124, 88, 188))
    make_enemy("zombie", (76, 126, 75), (116, 86, 62))
    make_enemy("skeleton", (198, 194, 164), (139, 132, 110))
    make_enemy("ghost", (126, 188, 213), (185, 231, 242))
    make_enemy("giant_bat", (75, 42, 112), (158, 92, 196), boss=True)
    make_enemy("armored_zombie", (103, 112, 104), (166, 168, 146), boss=True)
    make_enemy("necromancer", (54, 74, 148), (110, 90, 190), ranged=True)
    make_enemy("blood_guardian", (143, 48, 76), (218, 170, 78), boss=True)
    make_enemy("grave_warden", (74, 91, 150), (190, 196, 224), boss=True)
    make_enemy("bone_harvester", (180, 172, 132), (232, 218, 164), boss=True)
    make_enemy("vampire_count", (142, 34, 57), (232, 200, 92), boss=True)
    for name, colors in {
        "whip": [(130, 62, 68), (224, 78, 96), (255, 198, 146)],
        "knife": [(110, 116, 132), (226, 232, 238), (128, 170, 220)],
        "holy_book": [(166, 134, 64), (236, 214, 126), (255, 244, 182)],
        "fire_staff": [(142, 62, 40), (238, 98, 42), (255, 210, 82)],
        "magic_bolt": [(44, 83, 156), (96, 178, 245), (206, 232, 255)],
        "lightning_ring": [(78, 100, 160), (118, 216, 255), (252, 242, 132)],
        "blood_whip": [(150, 36, 64), (240, 45, 78), (255, 190, 190)],
        "thousand_blades": [(80, 90, 118), (230, 235, 240), (156, 204, 255)],
    }.items():
        make_icon(name, colors)
    make_passive_icon("hollow_sword", "sword")
    make_passive_icon("armor", "armor")
    make_passive_icon("focus_crystal", "crystal")
    make_passive_icon("clover", "clover")
    make_spinach()
    make_effect("effect_slash", (235, 72, 96))
    make_effect("effect_magic", (90, 180, 248))
    make_audio()
    pygame.quit()


if __name__ == "__main__":
    main()
