"""Snake – reine Spiellogik ohne Grafik (per unittest testbar)."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Optional

DIRS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}

MAX_QUEUE = 3
SPECIAL_CHANCE = 0.3
SPECIAL_TTL = 40          # Spielschritte, die das Spezialfutter liegen bleibt
POINTS_FOOD = 10
POINTS_SPECIAL = 50

Cell = tuple[int, int]

# Zustände
START, RUNNING, PAUSED, OVER, WON = "start", "running", "paused", "over", "won"


@dataclass
class Special:
    pos: Cell
    ttl: int = SPECIAL_TTL
    max_ttl: int = SPECIAL_TTL


def obstacle_layout(w: int, h: int) -> list[Cell]:
    """Feste, symmetrische Hindernisse; die Startzeile bleibt frei."""
    cells: list[Cell] = []
    y1, y2 = h // 4, h - 1 - h // 4
    xa, xb = w // 5, (w * 2) // 5 - 1
    for y in (y1, y2):
        cells += [(x, y) for x in range(xa, xb + 1)]
        cells += [(x, y) for x in range(w - 1 - xb, w - xa)]
    return cells


@dataclass
class Game:
    width: int = 20
    height: int = 20
    wrap: bool = False
    use_obstacles: bool = False
    use_special: bool = False
    rng: Callable[[], float] = random.random
    base_tick: int = 150      # ms pro Spielschritt am Anfang
    min_tick: int = 60
    tick_step: int = 4        # ms schneller pro gefressenem Futter

    # Laufzeitzustand (wird in reset() gesetzt)
    snake: list[Cell] = field(default_factory=list, init=False)   # Kopf zuerst
    direction: str = field(default="right", init=False)
    queue: list[str] = field(default_factory=list, init=False)
    obstacles: list[Cell] = field(default_factory=list, init=False)
    obstacle_set: set[Cell] = field(default_factory=set, init=False)
    food: Optional[Cell] = field(default=None, init=False)
    special: Optional[Special] = field(default=None, init=False)
    score: int = field(default=0, init=False)
    eaten: int = field(default=0, init=False)
    tick_ms: int = field(default=150, init=False)
    state: str = field(default=START, init=False)
    death_reason: Optional[str] = field(default=None, init=False)
    last_event: Optional[str] = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.reset()

    # ---------- Aufbau ----------
    def reset(self) -> None:
        cy, cx = self.height // 2, self.width // 4
        self.snake = [(cx + 2, cy), (cx + 1, cy), (cx, cy)]
        self.direction = "right"
        self.queue = []
        self.obstacles = obstacle_layout(self.width, self.height) if self.use_obstacles else []
        self.obstacle_set = set(self.obstacles)
        self.score = 0
        self.eaten = 0
        self.tick_ms = self.base_tick
        self.special = None
        self.food = None
        self.state = START
        self.death_reason = None
        self.last_event = None
        self.spawn_food()

    def free_cells(self) -> list[Cell]:
        occ = set(self.snake) | self.obstacle_set
        if self.food:
            occ.add(self.food)
        if self.special:
            occ.add(self.special.pos)
        return [(x, y) for y in range(self.height) for x in range(self.width) if (x, y) not in occ]

    def _pick(self, cells: list[Cell]) -> Cell:
        return cells[min(len(cells) - 1, int(self.rng() * len(cells)))]

    def spawn_food(self) -> bool:
        """Futter nur auf freie Zellen. False, wenn kein Platz mehr ist."""
        self.food = None
        free = self.free_cells()
        if free:
            self.food = self._pick(free)
            return True
        if self.special:
            self.food, self.special = self.special.pos, None
            return True
        return False

    def _maybe_spawn_special(self) -> None:
        if not self.use_special or self.special or self.rng() >= SPECIAL_CHANCE:
            return
        free = self.free_cells()
        if free:
            self.special = Special(self._pick(free))

    # ---------- Eingabe ----------
    def queue_direction(self, d: str) -> bool:
        """Richtungswunsch puffern. Geprüft gegen die zuletzt gepufferte Richtung,
        damit schnelle Doppeleingaben keine 180°-Umkehr ergeben."""
        if d not in DIRS or len(self.queue) >= MAX_QUEUE:
            return False
        last = self.queue[-1] if self.queue else self.direction
        if d == last or d == OPPOSITE[last]:
            return False
        self.queue.append(d)
        return True

    # ---------- Zustände ----------
    def start(self) -> None:
        if self.state == START:
            self.state = RUNNING

    def toggle_pause(self) -> None:
        if self.state == RUNNING:
            self.state = PAUSED
        elif self.state == PAUSED:
            self.state = RUNNING

    def restart(self) -> None:
        self.reset()
        self.state = RUNNING

    def _die(self, reason: str) -> str:
        self.state = OVER
        self.death_reason = reason
        self.last_event = OVER
        return OVER

    # ---------- Ein fester Spielschritt ----------
    def step(self) -> Optional[str]:
        if self.state != RUNNING:
            return None
        self.last_event = None

        # 1. Höchstens eine Richtungsänderung pro Schritt
        if self.queue:
            self.direction = self.queue.pop(0)

        # 2. Neuen Kopf berechnen
        dx, dy = DIRS[self.direction]
        hx, hy = self.snake[0]
        nx, ny = hx + dx, hy + dy
        if self.wrap:
            nx, ny = nx % self.width, ny % self.height
        elif not (0 <= nx < self.width and 0 <= ny < self.height):
            return self._die("wall")
        new_head = (nx, ny)

        eat_food = self.food == new_head
        eat_special = self.special is not None and self.special.pos == new_head
        grow = eat_food or eat_special

        # 3. Kollision prüfen
        if new_head in self.obstacle_set:
            return self._die("obstacle")
        # Schwanz-Sonderfall: ohne Wachstum wird die Schwanzzelle in diesem Schritt frei
        body = self.snake if grow else self.snake[:-1]
        if new_head in body:
            return self._die("self")

        # 4. Bewegen: wachsen oder Schwanz entfernen
        self.snake.insert(0, new_head)
        if not grow:
            self.snake.pop()

        if self.special and not eat_special:
            self.special.ttl -= 1
            if self.special.ttl <= 0:
                self.special = None
                self.last_event = "special_expired"
        if eat_special:
            self.score += POINTS_SPECIAL
            self.special = None
            self.last_event = "special"
        if eat_food:
            self.score += POINTS_FOOD
            self.last_event = "food"

        if grow:
            self.eaten += 1
            self.tick_ms = max(self.min_tick, self.base_tick - self.eaten * self.tick_step)
            # Gewinnbedingung: Schlange füllt alle begehbaren Zellen
            if len(self.snake) >= self.width * self.height - len(self.obstacles):
                self.state, self.food, self.special = WON, None, None
                self.last_event = WON
                return WON
            if eat_food:
                if not self.spawn_food():
                    self.state = WON
                    self.last_event = WON
                    return WON
                self._maybe_spawn_special()
        return self.last_event


# ---------- Bestenliste (Top 10 je Modus) ----------
MAX_SCORES = 10
NAME_MAX = 16
DEFAULT_NAME = "Anonym"


def clean_name(name: str) -> str:
    """Steuerzeichen entfernen, Leerraum zusammenfassen, auf NAME_MAX kürzen."""
    name = "".join(ch for ch in str(name) if ch.isprintable())
    name = " ".join(name.split())[:NAME_MAX].strip()
    return name or DEFAULT_NAME


def qualifies(scores: list[dict], score: int) -> bool:
    """Reicht die Punktzahl für einen Platz in der Bestenliste?"""
    return score > 0 and (len(scores) < MAX_SCORES or score > scores[MAX_SCORES - 1]["score"])


def insert_score(scores: list[dict], entry: dict) -> tuple[list[dict], Optional[int]]:
    """Eintrag einsortieren (bei Gleichstand bleibt der ältere vorn), auf MAX_SCORES kürzen.
    Gibt die neue Liste und den Platz (0-basiert) zurück, None wenn nicht in der Liste."""
    if not qualifies(scores, entry["score"]):
        return list(scores), None
    rank = next((i for i, e in enumerate(scores) if entry["score"] > e["score"]), len(scores))
    new = scores[:rank] + [entry] + scores[rank:]
    return new[:MAX_SCORES], rank
