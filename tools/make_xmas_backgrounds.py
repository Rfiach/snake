"""Erzeugt die weihnachtlichen Weltraum-Hintergründe in assets/ (xmas_01.png … xmas_08.png).

Nur zum (Neu-)Erzeugen nötig, nicht zum Spielen:
    py -m pip install --user numpy pillow
    py tools/make_xmas_backgrounds.py
Danach `py tools/embed_backgrounds.py` ausführen, damit index.html die Bilder enthält.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw

from make_backgrounds import OUT, SIZE, base, blob, comet, finish, galaxy, nebula, noise, planet, stars, xx, yy


def glow_line(img, x0, y0, x1, y1, color, width=0.0025, strength=1.0):
    """Leuchtende Linie (Abstandsfeld zu einem Segment)."""
    vx, vy = x1 - x0, y1 - y0
    t = np.clip(((xx - x0) * vx + (yy - y0) * vy) / (vx * vx + vy * vy + 1e-9), 0, 1)
    d = np.hypot(xx - (x0 + t * vx), yy - (y0 + t * vy))
    img += (np.exp(-(d / width) ** 2) * strength)[..., None] * np.array(color, np.float32)


def bright_star(img, cx, cy, size=1.0, color=(1.0, 0.92, 0.7)):
    """Großer Stern mit vier langen Strahlen (Stern von Bethlehem)."""
    dx, dy = np.abs(xx - cx), np.abs(yy - cy)
    rays = (np.exp(-dy * 600 / size) * np.exp(-dx * 9 / size) + np.exp(-dx * 600 / size) * np.exp(-dy * 9 / size))
    diag = (np.exp(-np.abs(dx - dy) * 500 / size) * np.exp(-(dx + dy) * 18 / size)) * 0.5
    core = blob(cx, cy, 0.01 * size) * 2 + blob(cx, cy, 0.05 * size) * 0.5
    img += (rays * 1.4 + diag + core)[..., None] * np.array(color, np.float32)


def aurora(img, rng, y0, colors, strength=1.0):
    """Polarlicht-Vorhang: unten scharfe Kante, nach oben ausfadend, senkrecht gestreift."""
    n = noise(rng, 4, 2)
    center = y0 + 0.06 * np.sin(xx * 7 + 1) + 0.04 * np.sin(xx * 17) + 0.05 * (n - 0.5)
    d = yy - center
    curtain = np.where(d < 0, np.exp(d / 0.2), np.exp(-d / 0.015))
    stripes = 0.55 + 0.45 * np.sin(xx * 90 + noise(rng, 3, 4) * 10)
    lo, hi = (np.array(c, np.float32) for c in colors)
    mix = np.clip(-d / 0.25, 0, 1)[..., None]               # unten Farbe 1, oben Farbe 2
    img += (curtain * stripes * strength)[..., None] * (lo * (1 - mix) + hi * mix)


def snowflake(img, cx, cy, r, color=(0.7, 0.85, 1.0), strength=0.9):
    """Sechsstrahlige Schneeflocke aus leuchtenden Linien."""
    for k in range(6):
        a = k * math.pi / 3
        ex, ey = cx + math.cos(a) * r, cy + math.sin(a) * r
        glow_line(img, cx, cy, ex, ey, color, 0.003, strength)
        for f, L in ((0.45, 0.32), (0.72, 0.22)):            # Seitenäste
            bx, by = cx + math.cos(a) * r * f, cy + math.sin(a) * r * f
            for s in (-1, 1):
                b = a + s * math.pi / 4
                glow_line(img, bx, by, bx + math.cos(b) * r * L, by + math.sin(b) * r * L, color, 0.0025, strength * 0.8)
    img += blob(cx, cy, r * 0.12)[..., None] * np.array(color, np.float32)


def silhouette(img, draw_fn, darkness=0.02):
    """Dunkle Silhouette (z. B. Rentierschlitten) über das Bild legen."""
    mask = Image.new("L", (SIZE, SIZE), 0)
    draw_fn(ImageDraw.Draw(mask), SIZE)
    m = (np.asarray(mask, np.float32) / 255)[..., None]
    img[:] = img * (1 - m) + darkness * m


def sleigh(d: ImageDraw.ImageDraw, s: int) -> None:
    P = lambda x, y: (x * s, y * s)
    # zwei Rentiere vorn, Schlitten hinten – alles leicht nach rechts oben fliegend
    for ox, oy in ((0.0, 0.0), (0.11, -0.03)):
        bx, by = 0.50 + ox, 0.40 + oy
        d.ellipse([*P(bx - 0.045, by - 0.018), *P(bx + 0.045, by + 0.018)], fill=255)          # Körper
        d.ellipse([*P(bx + 0.04, by - 0.04), *P(bx + 0.065, by - 0.018)], fill=255)            # Kopf
        d.line([P(bx + 0.035, by - 0.01), P(bx + 0.05, by - 0.03)], fill=255, width=int(s * 0.012))   # Hals
        for lx, dx in ((-0.03, -0.02), (-0.015, 0.0), (0.02, 0.015), (0.035, 0.03)):           # Beine
            d.line([P(bx + lx, by + 0.012), P(bx + lx + dx, by + 0.045)], fill=255, width=int(s * 0.006))
        for a in (-0.012, 0.01):                                                                # Geweih
            ax, ay = bx + 0.052 + a, by - 0.038
            d.line([P(ax, ay), P(ax - 0.01, ay - 0.03)], fill=255, width=int(s * 0.004))
            d.line([P(ax - 0.006, ay - 0.016), P(ax + 0.006, ay - 0.026)], fill=255, width=int(s * 0.003))
    # Zügel
    d.line([P(0.34, 0.45), P(0.50, 0.40), P(0.61, 0.37)], fill=255, width=int(s * 0.003))
    # Schlitten
    d.polygon([P(0.22, 0.43), P(0.36, 0.43), P(0.38, 0.47), P(0.25, 0.49), P(0.21, 0.46)], fill=255)
    d.line([P(0.20, 0.505), P(0.37, 0.505), P(0.40, 0.485)], fill=255, width=int(s * 0.006))   # Kufe
    d.line([P(0.25, 0.49), P(0.25, 0.505)], fill=255, width=int(s * 0.005))
    d.line([P(0.34, 0.47), P(0.34, 0.505)], fill=255, width=int(s * 0.005))
    d.ellipse([*P(0.235, 0.385), *P(0.29, 0.44)], fill=255)                                    # Geschenkesack


def main() -> None:
    OUT.mkdir(exist_ok=True)
    R = lambda s: np.random.default_rng(100 + s)
    RED, GREEN, GOLD = (1.0, 0.2, 0.25), (0.15, 1.0, 0.45), (1.0, 0.8, 0.3)

    # 1 Polarlicht über einem Eisplaneten
    rng = R(1); img = base((0.0, 0.01, 0.04), (0.0, 0.03, 0.06))
    stars(img, rng, 500, 10)
    aurora(img, rng, 0.55, (GREEN, RED), 0.9)
    planet(img, 0.5, 1.75, 1.0, (0.55, 0.7, 0.85), (0.9, 0.95, 1.0), rng, light=(0.0, -0.95))
    finish(img, "xmas_01.png")

    # 2 Sternbild in Tannenbaumform mit goldenem Stern an der Spitze
    rng = R(2); img = base((0.0, 0.03, 0.02), (0.0, 0.02, 0.04))
    nebula(img, rng, (0.1, 0.8, 0.4), 0.5, 0.55, 0.4, 1.1)
    stars(img, rng, 380, 6)
    tree = [(0.5, 0.2), (0.38, 0.38), (0.45, 0.38), (0.32, 0.56), (0.42, 0.56), (0.26, 0.76),
            (0.74, 0.76), (0.58, 0.56), (0.68, 0.56), (0.55, 0.38), (0.62, 0.38), (0.5, 0.2)]
    for (x0, y0), (x1, y1) in zip(tree, tree[1:]):
        glow_line(img, x0, y0, x1, y1, (0.5, 1.0, 0.6), 0.0018, 0.35)
    for x, y in tree[:-1]:
        img += blob(x, y, 0.006)[..., None] * np.array([1.0, 1.0, 0.9]) * 1.4
    glow_line(img, 0.47, 0.76, 0.47, 0.84, (0.9, 0.6, 0.3), 0.002, 0.4)
    glow_line(img, 0.53, 0.76, 0.53, 0.84, (0.9, 0.6, 0.3), 0.002, 0.4)
    bright_star(img, 0.5, 0.2, 0.6, GOLD)
    finish(img, "xmas_02.png")

    # 3 Stern von Bethlehem mit Schweif über tiefblauem Himmel
    rng = R(3); img = base((0.0, 0.0, 0.05), (0.01, 0.01, 0.08))
    nebula(img, rng, (0.2, 0.35, 1.0), 0.6, 0.45, 0.4, 0.9)
    stars(img, rng, 600, 12)
    comet(img, 0.95, 0.05, 0.62, 0.34)
    bright_star(img, 0.62, 0.34, 1.2)
    finish(img, "xmas_03.png", 0.66)

    # 4 Eisplanet mit Ring im roten Nebel
    rng = R(4); img = base((0.05, 0.0, 0.01), (0.03, 0.0, 0.03))
    nebula(img, rng, (1.0, 0.15, 0.2), 0.35, 0.4, 0.35, 1.3)
    nebula(img, rng, (1.0, 0.7, 0.3), 0.25, 0.3, 0.15, 0.6)
    stars(img, rng)
    planet(img, 0.68, 0.62, 0.17, (0.7, 0.85, 1.0), (0.95, 0.98, 1.0), rng, ring=2.0)
    finish(img, "xmas_04.png")

    # 5 Rentierschlitten vor dem Mond
    rng = R(5); img = base((0.0, 0.01, 0.05), (0.01, 0.02, 0.07))
    stars(img, rng, 450, 8)
    planet(img, 0.42, 0.42, 0.3, (0.75, 0.75, 0.7), (0.95, 0.95, 0.88), rng, light=(-0.2, -0.3))
    silhouette(img, sleigh)
    finish(img, "xmas_05.png")

    # 6 Planet als Christbaumkugel im rot-goldenen Nebel
    rng = R(6); img = base((0.04, 0.0, 0.01), (0.02, 0.01, 0.03))
    nebula(img, rng, (1.0, 0.55, 0.15), 0.55, 0.5, 0.4, 1.0)
    stars(img, rng)
    planet(img, 0.32, 0.6, 0.16, (0.6, 0.02, 0.05), (1.0, 0.25, 0.25), rng, light=(-0.5, -0.6))
    img += (np.exp(-((np.abs(xx - 0.32) / 0.03) ** 4 + (np.abs(yy - 0.43) / 0.018) ** 4)))[..., None] * np.array(GOLD) * 1.2
    glow_line(img, 0.32, 0.41, 0.32, 0.0, (0.9, 0.8, 0.6), 0.0015, 0.5)       # Aufhänger
    finish(img, "xmas_06.png")

    # 7 Rot-grüne Spiralgalaxie
    rng = R(7); img = base((0.0, 0.01, 0.02), (0.01, 0.0, 0.03))
    stars(img, rng, 650, 10)
    galaxy(img, rng, 0.5, 0.5, 0.3, (0.3, 1.0, 0.45))
    galaxy(img, rng, 0.5, 0.5, 0.18, (1.0, 0.3, 0.3))
    finish(img, "xmas_07.png")

    # 8 Schneeflocken-Nebel
    rng = R(8); img = base((0.0, 0.02, 0.06), (0.0, 0.01, 0.04))
    nebula(img, rng, (0.4, 0.6, 1.0), 0.5, 0.5, 0.45, 1.0)
    stars(img, rng, 500, 8)
    snowflake(img, 0.5, 0.5, 0.2)
    snowflake(img, 0.17, 0.22, 0.07, strength=0.6)
    snowflake(img, 0.84, 0.78, 0.09, strength=0.6)
    finish(img, "xmas_08.png")
    print("Weihnachts-Hintergründe erzeugt in", OUT)


if __name__ == "__main__":
    main()
