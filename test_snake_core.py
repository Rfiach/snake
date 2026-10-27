"""Tests der Pflichtanforderungen aus CLAUDE.md.  Ausführen: python -m unittest -v"""
import random
import unittest

from snake_core import DIRS, OVER, RUNNING, WON, Game, Special


def make(**kw) -> Game:
    g = Game(rng=lambda: 0.0, **kw)
    g.start()
    return g


class TestSnakeCore(unittest.TestCase):
    def test_no_reverse(self):
        g = make()
        self.assertFalse(g.queue_direction("left"))

    def test_double_input_no_reverse(self):
        g = make()
        g.food = (0, 0)
        g.queue_direction("up")
        g.queue_direction("left")
        g.step(); self.assertEqual(g.direction, "up")
        g.step(); self.assertEqual(g.direction, "left")
        self.assertEqual(g.state, RUNNING)

    def test_queue_rejects_reverse_of_buffered(self):
        g = make()
        g.queue_direction("up")
        self.assertFalse(g.queue_direction("down"))

    def test_wall(self):
        g = make()
        g.food = (0, 0)
        for _ in range(30):
            g.step()
        self.assertEqual((g.state, g.death_reason), (OVER, "wall"))

    def test_wrap(self):
        g = make(wrap=True)
        g.food = (0, 0)
        for _ in range(30):
            g.step()
        self.assertEqual(g.state, RUNNING)

    def test_eat_grows(self):
        g = make()
        hx, hy = g.snake[0]
        g.food = (hx + 1, hy)
        g.step()
        self.assertEqual(len(g.snake), 4)
        self.assertEqual(g.score, 10)
        self.assertNotIn(g.food, g.snake)
        self.assertLess(g.tick_ms, g.base_tick)

    def test_tail_special_case_allowed(self):
        g = make()
        g.snake = [(5, 5), (6, 5), (6, 6), (5, 6)]
        g.direction, g.food = "left", (0, 0)
        g.queue_direction("down")
        g.step()
        self.assertEqual(g.state, RUNNING)

    def test_tail_special_case_with_growth_dies(self):
        g = make()
        g.snake = [(5, 5), (6, 5), (6, 6), (5, 6)]
        g.direction, g.food = "left", (5, 6)
        g.queue_direction("down")
        g.step()
        self.assertEqual((g.state, g.death_reason), (OVER, "self"))

    def test_obstacle(self):
        g = make(use_obstacles=True)
        ox, oy = g.obstacles[0]
        g.snake = [(ox, oy + 1), (ox, oy + 2), (ox, oy + 3)]
        g.direction, g.food = "up", (0, 0)
        g.step()
        self.assertEqual(g.death_reason, "obstacle")

    def test_spawn_never_on_snake_or_obstacle(self):
        for _ in range(200):
            g = Game(use_obstacles=True, use_special=True)
            self.assertTrue(set(g.snake).isdisjoint(g.obstacle_set))
            self.assertNotIn(g.food, g.obstacle_set)
            self.assertNotIn(g.food, g.snake)

    def test_landscape_board(self):
        g = make(width=28, height=18, use_obstacles=True)
        self.assertTrue(set(g.snake).isdisjoint(g.obstacle_set))
        self.assertTrue(all(0 <= x < 28 and 0 <= y < 18 for x, y in g.obstacles))
        # Wand liegt erst bei x = 28, nicht bei 20
        g = make(width=28, height=18)
        g.food = (0, 0)
        hx = g.snake[0][0]
        for _ in range(27 - hx):
            g.step()
        self.assertEqual(g.state, RUNNING)
        g.step()
        self.assertEqual((g.state, g.death_reason), (OVER, "wall"))

    def test_win_full_board(self):
        g = Game(width=3, height=2, rng=lambda: 0.0)
        g.start()
        g.snake = [(1, 0), (0, 0), (0, 1), (1, 1), (2, 1)]
        g.direction, g.food = "right", (2, 0)
        self.assertEqual(g.step(), WON)

    def test_special_expires(self):
        g = make(use_special=True, wrap=True)
        g.special = Special((0, 0), ttl=2, max_ttl=2)
        g.food = (19, 0)
        g.step(); g.step()
        self.assertIsNone(g.special)

    def test_special_points_and_growth(self):
        g = make(use_special=True)
        hx, hy = g.snake[0]
        g.special = Special((hx + 1, hy), ttl=9, max_ttl=9)
        g.food = (0, 0)
        g.step()
        self.assertEqual((g.score, len(g.snake)), (50, 4))

    def test_pause_stops(self):
        g = make()
        g.toggle_pause()
        before = list(g.snake)
        g.step()
        self.assertEqual(g.snake, before)

    def test_restart_resets(self):
        g = make()
        g.score, g.tick_ms = 99, 70
        g.restart()
        self.assertEqual((g.score, g.tick_ms, len(g.snake), g.state), (0, g.base_tick, 3, RUNNING))

    def test_fuzz(self):
        rnd = random.Random(1)
        for r in range(300):
            g = Game(wrap=bool(r % 2), use_obstacles=r % 3 == 0, use_special=True, rng=rnd.random)
            g.start()
            for _ in range(2000):
                if g.state != RUNNING:
                    break
                g.queue_direction(rnd.choice(list(DIRS)))
                g.step()
                self.assertEqual(len(set(g.snake)), len(g.snake))
                if g.food:
                    self.assertNotIn(g.food, g.snake)


if __name__ == "__main__":
    unittest.main()
