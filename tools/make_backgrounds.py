"""Erzeugt die Weltraum-Hintergründe in assets/ (bg_01.png … bg_08.png).

Nur zum (Neu-)Erzeugen nötig, nicht zum Spielen:
    py -m pip install --user numpy pillow
    py tools/make_backgrounds.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

SIZE = 480
OUT = Path(__file__).resolve().parent.parent / "assets"
yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32) / SIZE   # 0..1


def noise(rng, octaves=6, base=4):
    """Fraktales Rauschen 0..1 (Value-Noise, bilinear hochskaliert)."""
    total = np.zeros((SIZE, SIZE), np.float32)
    amp, norm = 1.0, 0.0
    for o in range(octaves):
        n = base * 2 ** o
        grid = rng.random((n + 1, n + 1)).astype(np.float32)
        img = Image.fromarray((grid * 255).astype(np.uint8)).resize((SIZE, SIZE), Image.BICUBIC)
        total += amp * np.asarray(img, np.float32) / 255
        norm += amp
        amp *= 0.55
    total /= norm
    return (total - total.min()) / (total.max() - total.min() + 1e-6)


def blob(cx, cy, r):
    return np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r)))


def nebula(img, rng, color, cx, cy, r, strength=1.0, sharp=2.2):
    n = noise(rng) ** sharp
    mask = (n * blob(cx, cy, r) * strength)[..., None]
    img += mask * np.array(color, np.float32)


def stars(img, rng, count=420, big=14):
    for _ in range(count):
        x, y = rng.integers(0, SIZE, 2)
        b = rng.random() ** 3
        tint = np.array([1.0, 1.0, 1.0]) - rng.random() * np.array([0.25, 0.1, 0.0]) * rng.choice([-1, 1])
        img[y, x] += tint * (0.35 + 0.65 * b)
    for _ in range(big):  # helle Sterne mit Glühen und Strahlen
        cx, cy = rng.random(2)
        g = blob(cx, cy, 0.006) * 1.2 + blob(cx, cy, 0.02) * 0.25
        ray = (np.exp(-np.abs(yy - cy) * 900) * np.exp(-np.abs(xx - cx) * 40) +
               np.exp(-np.abs(xx - cx) * 900) * np.exp(-np.abs(yy - cy) * 40)) * 0.5
        img += ((g + ray) * (0.5 + rng.random() * 0.5))[..., None] * np.array([1.0, 0.97, 0.9])


def planet(img, cx, cy, r, c1, c2, rng, ring=None, light=(-0.6, -0.6)):
    dx, dy = (xx - cx) / r, (yy - cy) / r
    d2 = dx * dx + dy * dy
    inside = d2 <= 1
    z = np.sqrt(np.clip(1 - d2, 0, 1))
    lx, ly = light
    lz = np.sqrt(max(0.0, 1 - lx * lx - ly * ly))
    shade = np.clip(dx * lx + dy * ly + z * lz, 0, 1) ** 0.9
    bands = 0.5 + 0.5 * np.sin(dy * 9 + noise(rng, 4, 3) * 4)
    col = np.array(c1) * (1 - bands[..., None]) + np.array(c2) * bands[..., None]
    surf = col * (0.06 + 0.94 * shade[..., None])
    atmo = np.exp(-np.abs(np.sqrt(d2) - 1) * 18)[..., None] * np.array(c2) * 0.5
    img[:] = np.where(inside[..., None], surf, img) + atmo * (~inside)[..., None]
    if ring:
        rx, ry = (xx - cx) / (r * ring), (yy - cy) / (r * ring * 0.28)
        rd = np.sqrt(rx * rx + ry * ry)
        band = (np.exp(-((rd - 0.85) ** 2) / 0.004) + 0.6 * np.exp(-((rd - 1.0) ** 2) / 0.002))
        front = (yy > cy) | ~inside      # Ring vor dem Planeten nur unten sichtbar
        img += (band * front)[..., None] * np.array([0.75, 0.65, 0.5]) * 0.8


def galaxy(img, rng, cx, cy, scale, color):
    dx, dy = (xx - cx) / scale, (yy - cy) / (scale * 0.55)
    rad = np.sqrt(dx * dx + dy * dy) + 1e-6
    ang = np.arctan2(dy, dx)
    arms = (0.5 + 0.5 * np.cos(2 * (ang - np.log(rad) * 2.6))) ** 3
    n = noise(rng, 5, 6)
    disc = np.exp(-rad * 2.2) * arms * (0.6 + 0.8 * n)
    core = np.exp(-rad * rad * 60)
    img += disc[..., None] * np.array(color) * 1.6 + core[..., None] * np.array([1.0, 0.9, 0.7]) * 1.1


def black_hole(img, cx, cy, r):
    dx, dy = xx - cx, (yy - cy) / 0.35
    d = np.sqrt(dx * dx + dy * dy)
    disk = np.exp(-((d - r * 1.9) ** 2) / (2 * (r * 0.55) ** 2)) * (np.abs(yy - cy) < r * 1.2)
    halo = np.exp(-((np.hypot(xx - cx, yy - cy) - r * 1.12) ** 2) / (2 * (r * 0.12) ** 2))
    img += disk[..., None] * np.array([1.0, 0.55, 0.2]) * 1.2 + halo[..., None] * np.array([1.0, 0.8, 0.5])
    hole = np.hypot(xx - cx, yy - cy) < r
    img[hole] = 0


def comet(img, x0, y0, x1, y1):
    vx, vy = x1 - x0, y1 - y0
    L = np.hypot(vx, vy)
    t = ((xx - x0) * vx + (yy - y0) * vy) / (L * L)
    px, py = x0 + t * vx, y0 + t * vy
    dist = np.hypot(xx - px, yy - py)
    tail = np.clip(t, 0, 1) ** 2 * np.exp(-dist / (0.002 + 0.012 * np.clip(t, 0, 1))) * (t >= 0) * (t <= 1.02)
    img += tail[..., None] * np.array([0.7, 0.9, 1.0]) * 1.3 + blob(x1, y1, 0.008)[..., None] * 1.5


def base(c_top, c_bot):
    return (np.array(c_top, np.float32) * (1 - yy[..., None]) + np.array(c_bot, np.float32) * yy[..., None]).copy()


def finish(img, name, max_bright=0.62):
    img = np.clip(img, 0, None)
    img = 1 - np.exp(-img * 1.4)                 # weiches Tonemapping
    img = img / img.max() * max_bright           # bewusst dunkel halten -> Schlange bleibt gut sichtbar
    vign = 1 - 0.45 * (((xx - 0.5) ** 2 + (yy - 0.5) ** 2) / 0.5)
    img *= vign[..., None]
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(OUT / name, optimize=True)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    R = lambda s: np.random.default_rng(s)

    # 1 Violetter Nebel
    rng = R(1); img = base((0.02, 0.0, 0.06), (0.05, 0.0, 0.08))
    nebula(img, rng, (0.7, 0.2, 1.0), 0.45, 0.45, 0.35, 1.4)
    nebula(img, rng, (1.0, 0.3, 0.6), 0.65, 0.6, 0.25, 0.9)
    stars(img, rng); finish(img, "bg_01.png")

    # 2 Blauer Nebel mit Ringplanet
    rng = R(2); img = base((0.0, 0.02, 0.07), (0.0, 0.03, 0.1))
    nebula(img, rng, (0.2, 0.5, 1.0), 0.3, 0.3, 0.4, 1.3)
    stars(img, rng)
    planet(img, 0.72, 0.68, 0.16, (0.75, 0.55, 0.35), (0.95, 0.8, 0.55), rng, ring=2.1)
    finish(img, "bg_02.png")

    # 3 Roter Nebel mit großem Mond in der Ecke
    rng = R(3); img = base((0.06, 0.0, 0.0), (0.04, 0.01, 0.02))
    nebula(img, rng, (1.0, 0.3, 0.1), 0.6, 0.35, 0.35, 1.4)
    nebula(img, rng, (1.0, 0.7, 0.2), 0.7, 0.3, 0.15, 0.7)
    stars(img, rng)
    planet(img, 0.05, 0.98, 0.34, (0.45, 0.45, 0.5), (0.7, 0.7, 0.75), rng, light=(0.7, -0.6))
    finish(img, "bg_03.png")

    # 4 Spiralgalaxie
    rng = R(4); img = base((0.0, 0.0, 0.03), (0.01, 0.0, 0.04))
    stars(img, rng, 500, 10)
    galaxy(img, rng, 0.5, 0.5, 0.32, (0.55, 0.65, 1.0))
    finish(img, "bg_04.png")

    # 5 Grüner Nebel mit zwei kleinen Planeten
    rng = R(5); img = base((0.0, 0.04, 0.03), (0.0, 0.02, 0.05))
    nebula(img, rng, (0.1, 1.0, 0.6), 0.5, 0.55, 0.38, 1.2)
    nebula(img, rng, (0.2, 0.6, 1.0), 0.3, 0.7, 0.2, 0.8)
    stars(img, rng)
    planet(img, 0.82, 0.18, 0.07, (0.9, 0.4, 0.3), (1.0, 0.7, 0.5), rng)
    planet(img, 0.16, 0.22, 0.04, (0.4, 0.8, 0.9), (0.7, 0.95, 1.0), rng)
    finish(img, "bg_05.png")

    # 6 Sternenfeld mit blauem Planeten von unten
    rng = R(6); img = base((0.0, 0.0, 0.02), (0.0, 0.02, 0.06))
    stars(img, rng, 700, 18)
    planet(img, 0.5, 1.55, 0.75, (0.1, 0.3, 0.7), (0.3, 0.7, 0.9), rng, light=(0.0, -0.95))
    finish(img, "bg_06.png")

    # 7 Schwarzes Loch im türkisen Nebel
    rng = R(7); img = base((0.0, 0.03, 0.04), (0.0, 0.01, 0.03))
    nebula(img, rng, (0.1, 0.8, 0.9), 0.5, 0.5, 0.45, 1.0)
    stars(img, rng)
    black_hole(img, 0.5, 0.5, 0.07)
    finish(img, "bg_07.png")

    # 8 Rosa-goldener Nebel mit Komet
    rng = R(8); img = base((0.05, 0.0, 0.04), (0.03, 0.01, 0.03))
    nebula(img, rng, (1.0, 0.4, 0.7), 0.4, 0.6, 0.35, 1.3)
    nebula(img, rng, (1.0, 0.8, 0.3), 0.65, 0.4, 0.2, 0.8)
    stars(img, rng)
    comet(img, 0.05, 0.1, 0.62, 0.42)
    finish(img, "bg_08.png")
    print("Hintergründe erzeugt in", OUT)


if __name__ == "__main__":
    main()
