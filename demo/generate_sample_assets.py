"""
Generates synthetic high-fidelity Bangladeshi canteen dish images for demo replay and testing.
Includes realistic plate rims, rice textures, dal, chicken curry, and vegetables.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import math

DEMO_DIR = Path(__file__).resolve().parent
ASSETS_DIR = DEMO_DIR / "sample_plates"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def draw_plate_base(draw, size=640):
    # Canteen table background (warm textured gray)
    # Plate rim (melamine / steel off-white)
    margin = 50
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=(242, 241, 238),
        outline=(205, 202, 195),
        width=5
    )
    # Inner rim
    inner_margin = margin + 30
    draw.ellipse(
        [inner_margin, inner_margin, size - inner_margin, size - inner_margin],
        fill=(248, 247, 245),
        outline=(220, 218, 212),
        width=2
    )


def create_empty_plate():
    img = Image.new("RGB", (640, 640), (225, 224, 220))
    draw = ImageDraw.Draw(img)
    draw_plate_base(draw)
    # Slight oil smudge / clean dish water reflection
    draw.arc([180, 200, 360, 380], start=30, end=150, fill=(230, 228, 220), width=3)
    out_path = ASSETS_DIR / "plate_01_clean_empty.jpg"
    img.save(out_path, quality=90)
    return out_path


def create_rice_chicken_leftover():
    img = Image.new("RGB", (640, 640), (225, 224, 220))
    draw = ImageDraw.Draw(img)
    draw_plate_base(draw)
    
    # Leftover plain rice patch (white/ivory grains)
    draw.ellipse([140, 180, 360, 460], fill=(255, 253, 245), outline=(225, 220, 205), width=2)
    for _ in range(80):
        # grain specks
        import random
        rx = random.randint(160, 340)
        ry = random.randint(200, 440)
        if (rx - 250)**2 / 100**2 + (ry - 320)**2 / 130**2 < 0.8:
            draw.line([rx, ry, rx + 4, ry + 2], fill=(235, 230, 215), width=2)

    # Chicken curry gravy & bone scraps (deep reddish-brown / turmeric yellow)
    draw.ellipse([340, 220, 520, 420], fill=(185, 75, 25), outline=(145, 55, 18), width=2)
    # Chicken bone piece
    draw.rounded_rectangle([390, 280, 470, 320], radius=8, fill=(215, 175, 130), outline=(130, 50, 15), width=2)
    
    out_path = ASSETS_DIR / "plate_02_rice_chicken_leftover.jpg"
    img.save(out_path, quality=90)
    return out_path


def create_khichuri_egg_leftover():
    img = Image.new("RGB", (640, 640), (225, 224, 220))
    draw = ImageDraw.Draw(img)
    draw_plate_base(draw)

    # Bhuna khichuri (golden yellow-orange rice & lentils)
    draw.ellipse([160, 160, 460, 480], fill=(215, 165, 35), outline=(175, 130, 25), width=3)
    # Egg curry half
    draw.ellipse([380, 280, 490, 390], fill=(235, 140, 30), outline=(170, 70, 15), width=2)
    draw.ellipse([410, 310, 460, 360], fill=(255, 210, 40))

    out_path = ASSETS_DIR / "plate_03_khichuri_egg_leftover.jpg"
    img.save(out_path, quality=90)
    return out_path


def create_dal_vegetable_leftover():
    img = Image.new("RGB", (640, 640), (225, 224, 220))
    draw = ImageDraw.Draw(img)
    draw_plate_base(draw)

    # Dal smear (yellowish lentil broth)
    draw.ellipse([160, 180, 360, 350], fill=(225, 190, 60), outline=(195, 160, 40), width=2)
    # Vegetable leftover (greens and potatoes)
    draw.ellipse([280, 320, 470, 480], fill=(95, 135, 55), outline=(70, 105, 40), width=2)

    out_path = ASSETS_DIR / "plate_04_dal_vegetable_leftover.jpg"
    img.save(out_path, quality=90)
    return out_path


def create_full_untouched_plate():
    img = Image.new("RGB", (640, 640), (225, 224, 220))
    draw = ImageDraw.Draw(img)
    draw_plate_base(draw)

    # Large mound of rice covering 60% of plate
    draw.ellipse([120, 120, 520, 520], fill=(255, 254, 248), outline=(225, 220, 210), width=2)
    # Fish curry whole piece & thick gravy
    draw.ellipse([300, 200, 510, 420], fill=(180, 80, 30), outline=(135, 55, 20), width=2)
    draw.ellipse([330, 240, 470, 340], fill=(130, 65, 30), outline=(90, 40, 15), width=2)

    out_path = ASSETS_DIR / "plate_05_untouched_full.jpg"
    img.save(out_path, quality=90)
    return out_path


if __name__ == "__main__":
    p1 = create_empty_plate()
    p2 = create_rice_chicken_leftover()
    p3 = create_khichuri_egg_leftover()
    p4 = create_dal_vegetable_leftover()
    p5 = create_full_untouched_plate()
    print(f"Generated 5 sample plate images in {ASSETS_DIR}")

