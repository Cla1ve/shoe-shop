"""Рисует учебные картинки обуви для static/uploads и заглушку picture.png.

Картинки есть не у всех товаров: у последних моделей файла нет специально, чтобы проверить заглушку.
Запуск из корня проекта:  python tools/make_images.py
Нужен Pillow (только для этого скрипта).
"""
import os

from PIL import Image, ImageDraw, ImageFilter

OUT = os.path.join("static", "uploads")
S = 2                      # рисуем в двойном размере для гладких краёв
W, H = 400 * S, 300 * S

# (категория, подходящее слово в названии) -> форма
SHAPES = {"Туфли": "heel", "Балетки": "flat", "Лоферы": "flat", "Мокасины": "flat", "Ботильоны": "boot", "Ботинки": "boot",
          "Сапоги": "tall", "Босоножки": "sandal", "Сандалии": "sandal"}
BG = {"Женская обувь": (252, 236, 240), "Мужская обувь": (232, 238, 246), "Детская обувь": (255, 244, 214), "Спортивная обувь": (230, 244, 236)}
COLORS = {
    "Женская обувь": [(178, 52, 92), (140, 60, 90), (205, 150, 120), (60, 60, 80), (200, 80, 110)],
    "Мужская обувь": [(92, 60, 40), (40, 40, 48), (120, 80, 50), (70, 80, 100), (60, 90, 70)],
    "Детская обувь": [(232, 89, 12), (60, 130, 220), (60, 170, 110), (220, 70, 120)],
    "Спортивная обувь": [(30, 90, 200), (230, 70, 40), (30, 30, 36), (20, 140, 110), (240, 170, 20)],
}


def p(points):
    return [(x * S, y * S) for x, y in points]


def draw_shoe(shape, color, sole):
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    dark = tuple(max(0, c - 40) for c in color)
    light = tuple(min(255, c + 45) for c in color)
    if shape == "sneaker":
        d.polygon(p([(65, 175), (75, 95), (125, 85), (165, 112), (215, 122), (290, 132), (345, 165), (352, 188), (65, 188)]), fill=color)
        d.polygon(p([(165, 112), (215, 122), (290, 132), (330, 155), (250, 150), (190, 140)]), fill=light)
        for x in (180, 205, 230):
            d.line(p([(x, 120), (x + 18, 142)]), fill=(255, 255, 255), width=4 * S)
        d.rounded_rectangle(p([(55, 184), (360, 212)]), 12 * S, fill=sole)
    elif shape == "boot":
        d.polygon(p([(85, 40), (190, 40), (196, 120), (262, 140), (345, 170), (352, 190), (80, 190)]), fill=color)
        d.polygon(p([(85, 40), (190, 40), (190, 60), (85, 60)]), fill=dark)
        d.rounded_rectangle(p([(72, 184), (362, 214)]), 10 * S, fill=sole)
    elif shape == "tall":
        d.polygon(p([(90, 20), (200, 20), (205, 125), (270, 148), (345, 172), (352, 192), (85, 192)]), fill=color)
        d.polygon(p([(90, 20), (200, 20), (200, 45), (90, 45)]), fill=light)
        d.rounded_rectangle(p([(76, 188), (362, 216)]), 10 * S, fill=sole)
    elif shape == "heel":
        d.polygon(p([(80, 180), (92, 120), (140, 142), (205, 168), (300, 172), (345, 186), (330, 198), (80, 198)]), fill=color)
        d.polygon(p([(85, 192), (118, 192), (108, 262), (90, 262)]), fill=dark)
        d.rounded_rectangle(p([(80, 190), (345, 204)]), 6 * S, fill=sole)
    elif shape == "flat":
        d.polygon(p([(70, 170), (80, 130), (150, 128), (220, 150), (320, 156), (355, 182), (70, 190)]), fill=color)
        d.ellipse(p([(150, 138), (200, 166)]), fill=(255, 255, 255))
        d.rounded_rectangle(p([(62, 186), (362, 206)]), 9 * S, fill=sole)
    else:                                  # sandal
        d.rounded_rectangle(p([(60, 190), (360, 214)]), 12 * S, fill=sole)
        for x0, x1, y in ((120, 190, 135), (190, 270, 150), (270, 330, 168)):
            d.line(p([(x0, 188), ((x0 + x1) / 2, y), (x1, 188)]), fill=color, width=14 * S)
        d.line(p([(80, 188), (86, 120)]), fill=color, width=14 * S)
    img = img.resize((400, 300), Image.LANCZOS)
    return img


def shape_for(name, cat):
    for word, shape in SHAPES.items():
        if name.startswith(word):
            return shape
    return "sneaker"


def main():
    from tools.make_import_files import PRODUCTS      # те же названия, что и в файле импорта
    os.makedirs(OUT, exist_ok=True)
    counters = {}
    for i, (name, cat, _man, *_rest) in enumerate(PRODUCTS, 1):
        if i > 27:
            continue                                    # у последних шести моделей картинки нет
        n = counters.get(cat, 0)
        counters[cat] = n + 1
        color = COLORS[cat][n % len(COLORS[cat])]
        sole = (250, 250, 250) if cat in ("Спортивная обувь", "Детская обувь") else (44, 44, 50)
        shoe = draw_shoe(shape_for(name, cat), color, sole)
        bg = Image.new("RGB", (400, 300), BG[cat])
        mask = Image.eval(shoe.convert("L"), lambda v: 0 if v > 250 else 255).filter(ImageFilter.GaussianBlur(0.8))
        bg.paste(shoe, (0, 0), mask)
        # мягкая тень под обувью
        bg.save(os.path.join(OUT, "IMG_%03d.png" % i), optimize=True)
    # заглушка
    ph = Image.new("RGB", (400, 300), (236, 238, 242))
    d = ImageDraw.Draw(ph)
    d.rounded_rectangle([110, 100, 290, 190], 16, outline=(160, 166, 178), width=5)
    d.polygon([(130, 175), (170, 130), (205, 160), (230, 140), (270, 175)], fill=(160, 166, 178))
    d.ellipse([235, 115, 262, 142], fill=(160, 166, 178))
    ph.save(os.path.join(OUT, "picture.png"), optimize=True)
    print("картинок:", len([f for f in os.listdir(OUT) if f.endswith(".png")]))


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.getcwd())
    main()
