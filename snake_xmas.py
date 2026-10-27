"""Snake – Weihnachts- und Silvester-Grafik für die pygame-Oberfläche (nur Optik).

Schnee, Feuerwerk, Funkeln, weihnachtliches Futter, Geschenk, Lichterketten-Schlange,
Weihnachtsmütze, Eisblöcke und Lichterketten-Rahmen. Gegenstück in index.html: Abschnitt „Weihnachten“.
"""
from __future__ import annotations

import math
import random

import pygame

RED, GREEN, GOLD, WHITE = (220, 38, 38), (22, 163, 74), (250, 204, 21), (248, 250, 252)
BULBS = [(239, 68, 68), (250, 204, 21), (34, 197, 94), (59, 130, 246), (236, 72, 153)]
BALLS = [(220, 38, 38), (234, 179, 8), (37, 99, 235), (147, 51, 234)]
FOOD_KINDS = ("candy", "gingerbread", "ball", "star", "cookie")

DEATH_TEXT = {"wall": "Gegen den Kamin gerumpelt.", "self": "In der eigenen Lichterkette verheddert.",
              "obstacle": "Am Eisblock festgefroren."}


def food_kind(eaten: int) -> str:
    return FOOD_KINDS[eaten % len(FOOD_KINDS)]


# ---------- Partikel ----------
class Snow:
    """Schneeflocken in drei Tiefenebenen mit leichtem Wind; burst() für ein kurzes Gestöber."""

    def __init__(self, rect: pygame.Rect, count: int = 140) -> None:
        self.rect, self.rng = rect, random.Random(7)
        self.flakes = [self._flake(random_y=True) for _ in range(count)]
        self.extra = 0.0                          # zusätzliche Flocken beim Gestöber (abklingend)

    def _flake(self, random_y: bool = False) -> list[float]:
        depth = self.rng.choice((0.4, 0.7, 1.0))
        y = self.rng.uniform(0, self.rect.h) if random_y else -4.0
        return [self.rng.uniform(0, self.rect.w), y, depth, self.rng.uniform(0, math.tau)]

    def burst(self) -> None:
        self.extra = 260.0

    def update(self, dt: float, now: int) -> None:
        wind = math.sin(now / 2400) * 18
        while len(self.flakes) < 140 + int(self.extra):
            self.flakes.append(self._flake())
        self.extra = max(0.0, self.extra - dt * 0.05)
        alive = []
        for f in self.flakes:
            x, y, depth, phase = f
            y += (22 + 38 * depth) * depth * dt / 1000
            x += (wind * depth + math.sin(now / 700 + phase) * 8) * dt / 1000
            if y > self.rect.h + 4:
                if len(alive) >= 140 + int(self.extra):
                    continue                      # Gestöber klingt ab
                x, y = self.rng.uniform(0, self.rect.w), -4.0
            f[0], f[1] = x % self.rect.w, y
            alive.append(f)
        self.flakes = alive

    def draw(self, surf: pygame.Surface) -> None:
        layer = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        for x, y, depth, _ in self.flakes:
            pygame.draw.circle(layer, (255, 255, 255, int(110 + 120 * depth)), (x, y), 0.8 + 1.8 * depth)
        surf.blit(layer, self.rect.topleft)


class Fireworks:
    """Silvester: Raketen steigen auf und zerplatzen in bunte Funken."""

    def __init__(self, rect: pygame.Rect) -> None:
        self.rect, self.rng = rect, random.Random(31)
        self.rockets: list[list[float]] = []      # x, y, vy, Farbe-Index
        self.sparks: list[list[float]] = []       # x, y, vx, vy, Lebenszeit, Farbe-Index
        self.next_in = 300.0

    def burst(self) -> None:
        for _ in range(4):
            self._explode(self.rng.uniform(0.2, 0.8) * self.rect.w, self.rng.uniform(0.2, 0.5) * self.rect.h)

    def _explode(self, x: float, y: float) -> None:
        col = self.rng.randrange(len(BULBS))
        for i in range(48):
            a, v = i / 48 * math.tau, self.rng.uniform(60, 150)
            self.sparks.append([x, y, math.cos(a) * v, math.sin(a) * v, self.rng.uniform(900, 1500), col])

    def update(self, dt: float, now: int) -> None:
        s = dt / 1000
        self.next_in -= dt
        if self.next_in <= 0:
            self.next_in = self.rng.uniform(500, 1300)
            self.rockets.append([self.rng.uniform(0.15, 0.85) * self.rect.w, self.rect.h, -self.rng.uniform(320, 420),
                                 self.rng.randrange(len(BULBS))])
        for r in self.rockets:
            r[1] += r[2] * s
            r[2] += 160 * s
        for r in [r for r in self.rockets if r[2] > -60 or r[1] < self.rect.h * 0.18]:
            self.rockets.remove(r)
            self._explode(r[0], r[1])
        for p in self.sparks:
            p[0] += p[2] * s; p[1] += p[3] * s
            p[3] += 70 * s; p[2] *= 0.985; p[4] -= dt
        self.sparks = [p for p in self.sparks if p[4] > 0]

    def draw(self, surf: pygame.Surface) -> None:
        layer = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        for x, y, _, _ in self.rockets:
            pygame.draw.circle(layer, (255, 230, 180, 230), (x, y), 2)
            pygame.draw.line(layer, (255, 200, 120, 120), (x, y), (x, y + 10), 2)
        for x, y, _, _, life, col in self.sparks:
            pygame.draw.circle(layer, (*BULBS[int(col)], int(min(255, life / 4))), (x, y), 2)
        surf.blit(layer, self.rect.topleft)


class Sparkles:
    """Kurzes Funkeln an der Stelle, an der gefressen wurde."""

    def __init__(self) -> None:
        self.items: list[list[float]] = []        # x, y, vx, vy, Lebenszeit
        self.rng = random.Random(3)

    def add(self, x: float, y: float) -> None:
        for i in range(14):
            a, v = i / 14 * math.tau, self.rng.uniform(40, 90)
            self.items.append([x, y, math.cos(a) * v, math.sin(a) * v, 450.0])

    def update(self, dt: float) -> None:
        for p in self.items:
            p[0] += p[2] * dt / 1000; p[1] += p[3] * dt / 1000; p[4] -= dt
        self.items = [p for p in self.items if p[4] > 0]

    def draw(self, surf: pygame.Surface) -> None:
        for x, y, _, _, life in self.items:
            r = 1 + 2.5 * life / 450
            pygame.draw.line(surf, GOLD, (x - r, y), (x + r, y))
            pygame.draw.line(surf, GOLD, (x, y - r), (x, y + r))


# ---------- Futter ----------
def star_points(cx: float, cy: float, outer: float, inner: float, n: int = 5, rot: float = -math.pi / 2):
    return [(cx + math.cos(rot + i * math.pi / n) * (outer if i % 2 == 0 else inner),
             cy + math.sin(rot + i * math.pi / n) * (outer if i % 2 == 0 else inner)) for i in range(2 * n)]


def draw_food(surf: pygame.Surface, kind: str, center: tuple[float, float], cell: int, now: int, eaten: int) -> None:
    cx, cy = center
    bob = math.sin(now / 300) * cell * 0.04
    cy += bob
    if kind == "candy":                           # Zuckerstange
        w = max(3, int(cell * 0.18))
        pts = [(cx + cell * 0.08, cy + cell * 0.38), (cx + cell * 0.08, cy - cell * 0.12)]
        arc = pygame.Rect(0, 0, cell * 0.42, cell * 0.42)
        arc.center = (cx - cell * 0.13, cy - cell * 0.12)
        pygame.draw.line(surf, WHITE, *pts, w)
        pygame.draw.arc(surf, WHITE, arc, 0, math.pi, w)
        for i in range(4):                        # rote Streifen
            y = cy + cell * (0.3 - i * 0.14)
            pygame.draw.line(surf, RED, (cx + cell * 0.08 - w / 2, y + 2), (cx + cell * 0.08 + w / 2, y - 2), 3)
        pygame.draw.arc(surf, RED, arc.inflate(-w // 2, -w // 2), 0.4, 1.2, 3)
        pygame.draw.arc(surf, RED, arc.inflate(-w // 2, -w // 2), 1.9, 2.7, 3)
    elif kind == "gingerbread":                   # Lebkuchenmann
        brown, icing = (180, 104, 50), WHITE
        pygame.draw.circle(surf, brown, (cx, cy - cell * 0.2), cell * 0.15)
        body = pygame.Rect(0, 0, cell * 0.34, cell * 0.36)
        body.center = (cx, cy + cell * 0.06)
        pygame.draw.ellipse(surf, brown, body)
        for sx in (-1, 1):
            pygame.draw.line(surf, brown, (cx, cy - cell * 0.02), (cx + sx * cell * 0.34, cy - cell * 0.1), int(cell * 0.12))
            pygame.draw.line(surf, brown, (cx + sx * cell * 0.07, cy + cell * 0.18),
                             (cx + sx * cell * 0.2, cy + cell * 0.4), int(cell * 0.13))
            pygame.draw.circle(surf, (40, 20, 10), (cx + sx * cell * 0.05, cy - cell * 0.22), max(1, cell * 0.025))
        pygame.draw.circle(surf, icing, (cx, cy + cell * 0.0), max(1, cell * 0.03))
        pygame.draw.circle(surf, icing, (cx, cy + cell * 0.1), max(1, cell * 0.03))
        pygame.draw.arc(surf, icing, pygame.Rect(cx - cell * 0.07, cy - cell * 0.22, cell * 0.14, cell * 0.1),
                        math.pi * 1.1, math.pi * 1.9, 1)
    elif kind == "ball":                          # Christbaumkugel
        col = BALLS[(eaten // len(FOOD_KINDS)) % len(BALLS)]
        r = cell * 0.32
        pygame.draw.circle(surf, col, (cx, cy + cell * 0.05), r)
        pygame.draw.circle(surf, tuple(min(255, c + 90) for c in col), (cx - r * 0.35, cy - r * 0.25), r * 0.28)
        pygame.draw.rect(surf, (212, 175, 55), (cx - cell * 0.09, cy - r - cell * 0.04, cell * 0.18, cell * 0.1))
        pygame.draw.circle(surf, (212, 175, 55), (cx, cy - r - cell * 0.08), cell * 0.05, 1)
    elif kind == "star":                          # Zimtstern
        pygame.draw.polygon(surf, (160, 98, 45), star_points(cx, cy, cell * 0.44, cell * 0.2))
        pygame.draw.polygon(surf, (250, 245, 235), star_points(cx, cy, cell * 0.34, cell * 0.15))
    else:                                         # Plätzchen mit Schokostückchen
        pygame.draw.circle(surf, (214, 160, 90), (cx, cy), cell * 0.36)
        pygame.draw.circle(surf, (190, 135, 70), (cx, cy), cell * 0.36, 2)
        for ox, oy in ((-0.15, -0.1), (0.12, -0.14), (0.02, 0.06), (-0.12, 0.16), (0.16, 0.12)):
            pygame.draw.circle(surf, (70, 40, 20), (cx + ox * cell, cy + oy * cell), max(1, cell * 0.05))


def draw_gift(surf: pygame.Surface, center: tuple[float, float], cell: int) -> None:
    """Spezialfutter: Geschenk mit Schleife."""
    cx, cy = center
    box = pygame.Rect(0, 0, cell * 0.66, cell * 0.54)
    box.center = (cx, cy + cell * 0.1)
    pygame.draw.rect(surf, (220, 38, 38), box, border_radius=3)
    pygame.draw.rect(surf, (185, 28, 28), (box.x - 2, box.y - 2, box.w + 4, cell * 0.14), border_radius=2)
    pygame.draw.rect(surf, GOLD, (cx - cell * 0.06, box.y - 2, cell * 0.12, box.h + 2))
    for sx in (-1, 1):
        loop = pygame.Rect(0, 0, cell * 0.26, cell * 0.18)
        loop.center = (cx + sx * cell * 0.13, box.y - cell * 0.08)
        pygame.draw.ellipse(surf, GOLD, loop, max(2, cell // 12))


# ---------- Schlange ----------
def draw_lights_snake(surf: pygame.Surface, centers: list[tuple[float, float]], cell: int, now: int,
                      wrap_gap: float) -> None:
    """Körper als Lichterkette: dunkelgrünes Kabel mit bunten, sanft blinkenden Lämpchen (ohne Kopf)."""
    cable = (21, 66, 38)
    for a, b in zip(centers, centers[1:]):
        if math.dist(a, b) <= wrap_gap:           # bei Wrap-around keine Linie quer übers Feld
            pygame.draw.line(surf, cable, a, b, max(3, cell // 7))
    glow = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    for i, (x, y) in enumerate(centers[1:], start=1):
        col = BULBS[i % len(BULBS)]
        lit = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(now / 260 + i * 1.7))
        c = tuple(int(v * lit) for v in col)
        pygame.draw.circle(glow, (*col, int(70 * lit)), (x, y), cell * 0.5)
        bulb = pygame.Rect(0, 0, cell * 0.44, cell * 0.56)
        bulb.center = (x, y)
        pygame.draw.ellipse(surf, c, bulb)
        pygame.draw.rect(surf, (120, 120, 110), (x - cell * 0.09, bulb.top - cell * 0.06, cell * 0.18, cell * 0.1))
        pygame.draw.circle(surf, (255, 255, 255), (x - cell * 0.07, y - cell * 0.1), max(1, cell * 0.05))
    surf.blit(glow, (0, 0))


def draw_hat(surf: pygame.Surface, head: pygame.Rect, dx: int, now: int) -> None:
    """Weihnachtsmütze oben auf dem Kopf; die Spitze weht entgegen der Laufrichtung."""
    cell = head.w
    lean = -dx if dx else 1                       # bei senkrechter Bewegung nach rechts
    sway = math.sin(now / 250) * cell * 0.04
    base_y = head.top + cell * 0.08
    tip = (head.centerx + lean * cell * 0.55 + sway, head.top - cell * 0.6)
    left, right = (head.left + cell * 0.04, base_y), (head.right - cell * 0.04, base_y)
    pygame.draw.polygon(surf, RED, [left, right, tip])
    pygame.draw.line(surf, (153, 27, 27), (head.centerx - lean * cell * 0.05, base_y), tip, 1)   # Falte
    brim = pygame.Rect(head.left - cell * 0.06, base_y - cell * 0.12, cell * 1.12, cell * 0.26)
    pygame.draw.rect(surf, WHITE, brim, border_radius=int(cell * 0.13))
    pygame.draw.rect(surf, (186, 196, 210), brim, 1, border_radius=int(cell * 0.13))
    pygame.draw.circle(surf, WHITE, tip, cell * 0.15)
    pygame.draw.circle(surf, (186, 196, 210), tip, cell * 0.15, 1)


# ---------- Hindernisse & Rahmen ----------
def draw_ice(surf: pygame.Surface, r: pygame.Rect) -> None:
    ice = pygame.Surface(r.size, pygame.SRCALPHA)
    pygame.draw.rect(ice, (147, 197, 253, 190), ice.get_rect(), border_radius=4)
    pygame.draw.rect(ice, (224, 242, 254, 230), ice.get_rect(), 2, border_radius=4)
    pygame.draw.line(ice, (255, 255, 255, 200), (r.w * 0.2, r.h * 0.25), (r.w * 0.45, r.h * 0.2), 2)
    pygame.draw.line(ice, (255, 255, 255, 140), (r.w * 0.6, r.h * 0.7), (r.w * 0.8, r.h * 0.55), 2)
    surf.blit(ice, r.topleft)


def draw_light_frame(surf: pygame.Surface, r: pygame.Rect, now: int, step: int = 22) -> None:
    """Wrap-around-Rahmen als Lichterkette."""
    pts = ([(x, r.top) for x in range(r.left, r.right, step)] + [(r.right, y) for y in range(r.top, r.bottom, step)] +
           [(x, r.bottom) for x in range(r.right, r.left, -step)] + [(r.left, y) for y in range(r.bottom, r.top, -step)])
    pygame.draw.rect(surf, (21, 66, 38), r, 2)
    for i, p in enumerate(pts):
        lit = 0.5 + 0.5 * math.sin(now / 300 + i)
        col = tuple(int(c * (0.5 + 0.5 * lit)) for c in BULBS[i % len(BULBS)])
        pygame.draw.circle(surf, col, p, 3.5)
