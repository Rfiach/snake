"""Snake – pygame-Oberfläche.  Start: python snake.py  (vorher: pip install pygame)"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pygame

from snake_core import DIRS, OVER, PAUSED, RUNNING, START, WON, Game

# ---------- Layout & Farben ----------
CELL = 24
GRID = 20
BOARD = CELL * GRID              # 480 px
HUD_H = 70
FOOT_H = 70
PAD = 12
WIN_W = BOARD + 2 * PAD
WIN_H = HUD_H + BOARD + FOOT_H + PAD
BOARD_X, BOARD_Y = PAD, HUD_H

BG = (15, 23, 42)
PANEL = (30, 41, 59)
TEXT = (226, 232, 240)
MUTED = (148, 163, 184)
ACCENT = (34, 197, 94)
DANGER = (239, 68, 68)
GOLD = (250, 204, 21)
CHECK_A, CHECK_B = (11, 18, 32), (16, 26, 46)
OBST, OBST_HI = (71, 85, 105), (100, 116, 139)
WRAP_COL = (56, 189, 248)

KEYMAP = {
    pygame.K_UP: "up", pygame.K_DOWN: "down", pygame.K_LEFT: "left", pygame.K_RIGHT: "right",
    pygame.K_w: "up", pygame.K_s: "down", pygame.K_a: "left", pygame.K_d: "right",
}
DEATH_TEXT = {"wall": "Gegen die Wand gefahren.", "self": "In den eigenen Schwanz gebissen.",
              "obstacle": "Gegen ein Hindernis gestoßen."}

HIGHSCORE_FILE = Path(__file__).with_name("highscore.json")
ASSETS = Path(__file__).with_name("assets")
BG_FADE_MS = 400          # Überblendzeit beim Hintergrundwechsel
BG_DIM = 70               # Abdunklung (0–255) über dem Bild, damit die Schlange gut sichtbar bleibt


# ---------- Highscore (pro Optionskombination) ----------
def load_scores() -> dict:
    try:
        return json.loads(HIGHSCORE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_scores(scores: dict) -> None:
    try:
        HIGHSCORE_FILE.write_text(json.dumps(scores), encoding="utf-8")
    except OSError:
        pass


class App:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Snake")
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        self.clock = pygame.time.Clock()
        self.f_title = pygame.font.SysFont("segoeui,arial,dejavusans", 34, bold=True)
        self.f_big = pygame.font.SysFont("segoeui,arial,dejavusans", 24, bold=True)
        self.f_text = pygame.font.SysFont("segoeui,arial,dejavusans", 17)
        self.f_small = pygame.font.SysFont("segoeui,arial,dejavusans", 13)

        self.opts = {"wrap": False, "obstacles": False, "special": True}
        self.scores = load_scores()
        self.game = self.new_game()
        self.acc = 0.0
        self.flash_until = 0
        self.new_high = False

        # Weltraum-Hintergründe: wechseln bei jedem gefressenen Futter
        self.backgrounds = self.load_backgrounds()
        self.bg_index = 0
        self.bg_prev: int | None = None
        self.bg_fade_start = 0
        self.grid_overlay = self.make_grid_overlay()

    def load_backgrounds(self) -> list[pygame.Surface]:
        images = []
        for path in sorted(ASSETS.glob("bg_*.png")):
            try:
                img = pygame.image.load(str(path)).convert()
                images.append(pygame.transform.smoothscale(img, (BOARD, BOARD)))
            except (pygame.error, OSError):
                pass
        return images

    @staticmethod
    def make_grid_overlay() -> pygame.Surface:
        s = pygame.Surface((BOARD, BOARD), pygame.SRCALPHA)
        s.fill((0, 0, 0, BG_DIM))
        for i in range(1, GRID):
            pygame.draw.line(s, (255, 255, 255, 14), (i * CELL, 0), (i * CELL, BOARD))
            pygame.draw.line(s, (255, 255, 255, 14), (0, i * CELL), (BOARD, i * CELL))
        return s

    def next_background(self) -> None:
        if len(self.backgrounds) < 2:
            return
        self.bg_prev = self.bg_index
        self.bg_index = (self.bg_index + 1) % len(self.backgrounds)
        self.bg_fade_start = pygame.time.get_ticks()

    # ---------- Spielsteuerung ----------
    def mode_key(self) -> str:
        return "".join("1" if self.opts[k] else "0" for k in ("wrap", "obstacles", "special"))

    @property
    def high(self) -> int:
        return self.scores.get(self.mode_key(), 0)

    def new_game(self) -> Game:
        return Game(width=GRID, height=GRID, wrap=self.opts["wrap"],
                    use_obstacles=self.opts["obstacles"], use_special=self.opts["special"])

    def begin(self) -> None:
        if self.game.state in (OVER, WON):
            self.game = self.new_game()
        self.game.start()
        self.new_high = False
        self.acc = 0.0

    def toggle_option(self, name: str) -> None:
        # Optionen nur außerhalb eines laufenden Spiels ändern
        if self.game.state in (RUNNING, PAUSED):
            return
        self.opts[name] = not self.opts[name]
        self.game = self.new_game()

    def on_direction(self, d: str) -> None:
        if self.game.state == START:
            self.begin()
        if self.game.state == RUNNING:
            self.game.queue_direction(d)

    def on_game_end(self, ev: str) -> None:
        self.acc = 0.0
        if self.game.score > self.high:
            self.scores[self.mode_key()] = self.game.score
            save_scores(self.scores)
            self.new_high = True
        if ev == OVER:
            self.flash_until = pygame.time.get_ticks() + 600

    def handle_key(self, key: int) -> None:
        g = self.game
        if key in KEYMAP:
            self.on_direction(KEYMAP[key])
        elif key in (pygame.K_SPACE, pygame.K_p, pygame.K_ESCAPE):
            if g.state in (RUNNING, PAUSED):
                g.toggle_pause()
                self.acc = 0.0
            elif key == pygame.K_SPACE:
                self.begin()
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if g.state == PAUSED:
                g.toggle_pause()
                self.acc = 0.0
            elif g.state != RUNNING:
                self.begin()
        elif key == pygame.K_1:
            self.toggle_option("wrap")
        elif key == pygame.K_2:
            self.toggle_option("obstacles")
        elif key == pygame.K_3:
            self.toggle_option("special")

    # ---------- Hauptschleife: feste Spielschritte, unabhängig von der Bildrate ----------
    def run(self) -> None:
        focus_lost = getattr(pygame, "WINDOWFOCUSLOST", None)
        while True:
            dt = min(250, self.clock.tick(60))
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if e.type == pygame.KEYDOWN:
                    self.handle_key(e.key)
                elif focus_lost is not None and e.type == focus_lost and self.game.state == RUNNING:
                    self.game.toggle_pause()

            if self.game.state == RUNNING:
                self.acc += dt
                while self.acc >= self.game.tick_ms and self.game.state == RUNNING:
                    self.acc -= self.game.tick_ms
                    ev = self.game.step()
                    if ev in ("food", "special"):
                        self.next_background()
                    if ev in (OVER, WON):
                        self.on_game_end(ev)

            self.draw(pygame.time.get_ticks())
            pygame.display.flip()

    # ---------- Zeichnen ----------
    def text(self, s: str, font, color, center) -> None:
        surf = font.render(s, True, color)
        self.screen.blit(surf, surf.get_rect(center=center))

    def cell_rect(self, x: int, y: int, inset: float = 0) -> pygame.Rect:
        return pygame.Rect(BOARD_X + x * CELL + inset, BOARD_Y + y * CELL + inset,
                           CELL - 2 * inset, CELL - 2 * inset)

    def draw(self, now: int) -> None:
        self.screen.fill(BG)
        self.draw_hud()
        self.draw_board(now)
        self.draw_footer()
        if self.game.state != RUNNING:
            self.draw_overlay()

    def draw_hud(self) -> None:
        g = self.game
        boxes = [("PUNKTE", g.score), ("LÄNGE", len(g.snake)), ("HIGHSCORE", max(self.high, g.score))]
        bw = (BOARD - 2 * 8) // 3
        for i, (label, val) in enumerate(boxes):
            r = pygame.Rect(PAD + i * (bw + 8), 10, bw, HUD_H - 20)
            pygame.draw.rect(self.screen, PANEL, r, border_radius=8)
            self.text(label, self.f_small, MUTED, (r.centerx, r.y + 13))
            self.text(str(val), self.f_big, TEXT, (r.centerx, r.y + 34))

    def draw_board(self, now: int) -> None:
        g = self.game
        self.draw_background(now)

        # Hindernisse
        for ox, oy in g.obstacles:
            r = self.cell_rect(ox, oy, 1)
            pygame.draw.rect(self.screen, OBST, r, border_radius=4)
            pygame.draw.rect(self.screen, OBST_HI, (r.x + 3, r.y + 3, r.w - 6, 3))

        # Futter (pulsierend)
        if g.food:
            fx, fy = self.cell_rect(*g.food).center
            radius = CELL * 0.36 * (1 + 0.08 * math.sin(now / 150))
            pygame.draw.circle(self.screen, DANGER, (fx, fy), radius)
            pygame.draw.rect(self.screen, (22, 163, 74), (fx - 1, fy - CELL * 0.48, 3, CELL * 0.18))

        # Spezialfutter mit Restzeit-Ring
        if g.special:
            sp = g.special
            sx, sy = self.cell_rect(*sp.pos).center
            blink = sp.ttl < 10 and (now // 120) % 2 == 0
            if not blink:
                pts = []
                for i in range(10):
                    rr = CELL * (0.42 if i % 2 == 0 else 0.18)
                    a = -math.pi / 2 + i * math.pi / 5
                    pts.append((sx + math.cos(a) * rr, sy + math.sin(a) * rr))
                pygame.draw.polygon(self.screen, GOLD, pts)
            frac = sp.ttl / sp.max_ttl
            ring = pygame.Rect(0, 0, CELL, CELL)
            ring.center = (sx, sy)
            # pygame-Winkel laufen gegen den Uhrzeigersinn; Start oben
            pygame.draw.arc(self.screen, GOLD, ring, math.pi / 2, math.pi / 2 + 2 * math.pi * frac, 2)

        # Schlange in Regenbogenfarben, Farben laufen langsam durch
        shift = now / 20 if g.state == RUNNING else 0

        def rainbow(i: int) -> pygame.Color:
            c = pygame.Color(0, 0, 0)
            c.hsva = ((i * 28 - shift) % 360, 85, 100, 100)
            return c

        for i in range(len(g.snake) - 1, 0, -1):
            pygame.draw.rect(self.screen, rainbow(i), self.cell_rect(*g.snake[i], 1.5), border_radius=5)

        # Kopf deutlich abgesetzt: weiß mit Regenbogen-Rand, rot bei Game Over
        head = self.cell_rect(*g.snake[0], 0.5)
        pygame.draw.rect(self.screen, DANGER if g.state == OVER else (248, 250, 252), head, border_radius=7)
        if g.state != OVER:
            pygame.draw.rect(self.screen, rainbow(0), self.cell_rect(*g.snake[0], 2), width=3, border_radius=6)
        dx, dy = DIRS[g.direction]
        cx, cy = head.center
        px, py = -dy, dx
        for side in (-1, 1):
            ex = cx + dx * CELL * 0.18 + px * side * CELL * 0.22
            ey = cy + dy * CELL * 0.18 + py * side * CELL * 0.22
            pygame.draw.circle(self.screen, (203, 213, 225), (ex, ey), CELL * 0.13)
            pygame.draw.circle(self.screen, BG, (ex + dx * CELL * 0.05, ey + dy * CELL * 0.05), CELL * 0.06)

        # Rahmen: rot blinkend bei Game Over, gestrichelt im Wrap-Modus
        frame = pygame.Rect(BOARD_X - 3, BOARD_Y - 3, BOARD + 6, BOARD + 6)
        flashing = pygame.time.get_ticks() < self.flash_until
        pygame.draw.rect(self.screen, DANGER if flashing else PANEL, frame, width=3, border_radius=6)
        if g.wrap and not flashing:
            self.draw_dashed_frame(frame.inflate(-2, -2))

    def draw_background(self, now: int) -> None:
        g = self.game
        if not self.backgrounds:   # Fallback ohne Bilder: Schachbrett
            for y in range(g.height):
                for x in range(g.width):
                    pygame.draw.rect(self.screen, CHECK_B if (x + y) % 2 else CHECK_A, self.cell_rect(x, y))
            return
        cur = self.backgrounds[self.bg_index]
        t = (now - self.bg_fade_start) / BG_FADE_MS
        if self.bg_prev is not None and t < 1:
            self.screen.blit(self.backgrounds[self.bg_prev], (BOARD_X, BOARD_Y))
            cur.set_alpha(int(255 * t))
            self.screen.blit(cur, (BOARD_X, BOARD_Y))
            cur.set_alpha(None)
        else:
            self.bg_prev = None
            self.screen.blit(cur, (BOARD_X, BOARD_Y))
        self.screen.blit(self.grid_overlay, (BOARD_X, BOARD_Y))

    def draw_dashed_frame(self, r: pygame.Rect, dash: int = 6) -> None:
        for x in range(r.left, r.right, dash * 2):
            pygame.draw.line(self.screen, WRAP_COL, (x, r.top), (min(x + dash, r.right), r.top), 2)
            pygame.draw.line(self.screen, WRAP_COL, (x, r.bottom), (min(x + dash, r.right), r.bottom), 2)
        for y in range(r.top, r.bottom, dash * 2):
            pygame.draw.line(self.screen, WRAP_COL, (r.left, y), (r.left, min(y + dash, r.bottom)), 2)
            pygame.draw.line(self.screen, WRAP_COL, (r.right, y), (r.right, min(y + dash, r.bottom)), 2)

    def draw_footer(self) -> None:
        y0 = BOARD_Y + BOARD + 10
        r = pygame.Rect(PAD, y0, BOARD, 30)
        pygame.draw.rect(self.screen, PANEL, r, border_radius=8)
        labels = [("1", "Wrap-around", "wrap"), ("2", "Hindernisse", "obstacles"), ("3", "Spezialfutter", "special")]
        w = BOARD // 3
        locked = self.game.state in (RUNNING, PAUSED)
        for i, (k, name, key) in enumerate(labels):
            on = self.opts[key]
            col = (ACCENT if on else MUTED) if not locked else (MUTED if not on else (21, 128, 61))
            self.text(f"[{k}] {name}: {'an' if on else 'aus'}", self.f_small, col, (PAD + w * i + w // 2, r.centery))
        hint = "←↑→↓ / WASD steuern · Leertaste / P Pause · Enter Start/Neustart"
        if locked:
            hint = "Optionen änderbar vor dem Start / nach Spielende"
        self.text(hint, self.f_small, MUTED, (WIN_W // 2, y0 + 46))

    def draw_overlay(self) -> None:
        g = self.game
        shade = pygame.Surface((BOARD, BOARD), pygame.SRCALPHA)
        shade.fill((15, 23, 42, 200))
        self.screen.blit(shade, (BOARD_X, BOARD_Y))
        cx, cy = BOARD_X + BOARD // 2, BOARD_Y + BOARD // 2

        if g.state == START:
            title, col = "Snake", TEXT
            line = "Friss Futter, wachse – aber beiß dich nicht selbst!"
            hint = "Pfeiltasten / WASD / Enter zum Starten"
        elif g.state == PAUSED:
            title, col = "Pause", TEXT
            line = f"Punkte: {g.score}"
            hint = "Leertaste / P zum Fortsetzen"
        elif g.state == OVER:
            title, col = "Game Over", DANGER
            line = f"{DEATH_TEXT.get(g.death_reason, '')} Punkte: {g.score}"
            hint = "Neuer Highscore!" if self.new_high else "Enter / Leertaste für Neustart"
        else:  # WON
            title, col = "Gewonnen!", GOLD
            line = f"Das ganze Feld ist gefüllt. Punkte: {g.score}"
            hint = "Neuer Highscore!" if self.new_high else "Enter / Leertaste für Neustart"

        self.text(title, self.f_title, col, (cx, cy - 40))
        self.text(line, self.f_text, TEXT, (cx, cy + 4))
        self.text(hint, self.f_text, GOLD if self.new_high and g.state in (OVER, WON) else MUTED, (cx, cy + 34))


if __name__ == "__main__":
    App().run()
