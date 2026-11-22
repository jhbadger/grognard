"""Tests every game gets for nothing: the self-test's checks, every
screen drawn wide and upright, the player's moves and attacks through
the screen, saving and loading, computer games played out, and a fuzz
of random keys and taps.  GROGNARD_GAME names the game (the first one
otherwise); GROGNARD_FUZZ the number of fuzzed games."""

import os
import random
import unittest

import util
from grognard import play_out
from grognard.game import Dialog, TitleMode, Charts, DropMenu
from grognard.hexgrid import hid

NAME = os.environ.get('GROGNARD_GAME') or util.games()[0]
GD = util.load(NAME)
FUZZ = int(os.environ.get('GROGNARD_FUZZ', '3'))


class Checks(unittest.TestCase):
    def test_selftest(self):
        from grognard.rules import Engine
        e = Engine(GD, seed=1)
        self.assertEqual(e.board.problems, [])
        for u in e.units.values():
            for h in ([u.hex] if u.hex else []) + u.entry:
                self.assertTrue(e.board.on_map(h), '%s at %s' % (u.id,
                                                                 hid(h)))
        for s in e.side_ids:
            if getattr(GD, 'SUPPLY', {}).get(s):
                self.assertTrue(e.supply_sources(s)[0])

    def test_computer_games(self):
        for seed in (11, 12):
            e = play_out(GD, seed=seed)
            self.assertTrue(e.over)
            self.assertTrue(e.result)


class Screens(unittest.TestCase):
    def test_title_and_every_zoom(self):
        g = util.new_game(GD, side=None)
        g.modes.append(TitleMode())
        s = g.frame()
        self.assertEqual((s.w, s.h), (640, 480))
        g.pop()
        for z in range(3):
            g.view.set_zoom(z)
            g.frame()
        g.portrait = True
        s = g.frame()
        self.assertEqual((s.w, s.h), (360, 640))

    def test_menus_and_dialogs(self):
        g = util.new_game(GD, side=GD.SIDES[0]['id'])
        for i in range(len(g.menus())):
            g.open_menu(i)
            self.assertIsInstance(g.mode, DropMenu)
            g.frame()
            g.key('esc')
        for show in (g.show_help, g.show_log, g.show_score,
                     g.show_turn_track, g.show_about, g.show_charts):
            show()
            g.frame()
            g.key('esc')
            self.assertIs(g.mode, g.play, show.__name__)
        g.show_charts()
        self.assertIsInstance(g.mode, Charts)

    def test_every_widget(self):
        from grognard.widgets import WIDGETS, Layout
        g = util.new_game(GD, side=GD.SIDES[1]['id'])

        class All:
            PANELS = dict(right=list(WIDGETS), bottom=['unit', 'orders',
                                                       'log'])
        save = getattr(GD, 'PANELS', None)
        GD.PANELS = All.PANELS
        try:
            for portrait in (False, True):
                g.layout = Layout(g, portrait)
                g.portrait = portrait
                g.view.set_rect(g.layout.map)
                s = g.render()
                for wd, r in g.layout.items:
                    wd.tap(g, r[0] + r[2] // 2, r[1] + r[3] // 2, r)
                    while g.mode is not g.play:
                        g.key('esc')
                g.render()
        finally:
            if save is None:
                del GD.PANELS
            else:
                GD.PANELS = save
        del s


class Smooth(unittest.TestCase):
    def test_every_screen_with_smooth_text(self):
        """With a window that measures text (as Tk and Kivy do), every
        screen records its text instead of drawing it."""
        from grognard import font
        g = util.new_game(GD, side=GD.SIDES[0]['id'])
        g.measure = lambda s, scale: len(s) * 6 * scale
        self.addCleanup(font.set_metrics, None)
        s = g.frame()
        self.assertTrue(s.texts)
        for show in (g.show_help, g.show_charts, g.show_score):
            show()
            self.assertTrue(g.frame().texts)
            g.key('esc')
        for z in range(3):
            g.view.set_zoom(z)
            g.frame()
        g.portrait = True
        g.frame()
        g.toggle_text()
        self.assertIsNone(g.frame().texts)
        g.toggle_text()


class Playing(unittest.TestCase):
    def setUp(self):
        self.side = GD.ORDER[0] if hasattr(GD, 'ORDER') else \
            GD.SIDES[0]['id']
        self.g = util.new_game(GD, side=self.side, seed=3)

    def tap_hex(self, h):
        g = self.g
        g.view.show(h)
        g.tap(*g.view.to_screen(h))

    def test_move_undo_attack(self):
        g = self.g
        e = g.e
        self.assertEqual(e.side, self.side)
        # a unit that can move and is on top of its stack (in Pickett's
        # Charge only the guns can, on turn 1)
        movers = [u for u in e.alive(self.side) if u.mp > 0 and
                  g.play.stack_at(u.hex)[0] is u]
        u = movers[0]
        self.tap_hex(u.hex)
        self.assertEqual(g.play.sel, [u.id])
        reach = g.play.reach
        self.assertTrue(reach)
        # somewhere it can go that meets nobody: then undo it
        start = u.hex
        quiet = [h for h in reach if h not in e.enemy_zoc(u.side) and
                 h not in e.enemy_hexes(u.side)]
        if quiet:
            before = set(e.visible(self.side))
            self.tap_hex(quiet[0])
            self.assertEqual(u.hex, quiet[0])
            if set(e.visible(self.side)) == before:
                g.key('u')
                self.assertEqual(u.hex, start)
        g.key('e')
        self.assertEqual(e.phase, 'combat')
        ts = sorted(e.targets())
        if ts:
            self.tap_hex(ts[0])
            self.assertEqual(g.play.target, ts[0])
            o = g.play.planned_odds()
            g.frame()
            if o['final'] >= 0:
                g.key('a')
                self.assertIn(ts[0], e.hit)
                while isinstance(g.mode, Dialog):
                    g.key('enter')
                g.key('s')          # stay, if there was a choice
        while e.side == self.side and not e.over:   # any later phases
            g.key('e')
            while isinstance(g.mode, Dialog):
                g.key('enter')
        self.assertNotEqual(e.side, self.side)
        # the computer takes its turn
        for _ in range(3000):
            g.update(0.1)
            while isinstance(g.mode, Dialog) and not e.over:
                g.key('enter')
            if e.side == self.side or e.over:
                break
        self.assertTrue(e.side == self.side or e.over)

    def test_stack_strip(self):
        """Selecting a stack shows all its units in a strip, and tapping
        one there selects it."""
        g = self.g
        e = g.e
        stacks = [h for h, us in e.where().items()
                  if len(g.play.stack_at(h)) > 1]
        if not stacks:
            self.skipTest('no stacks at the start')
        h = stacks[0]
        self.tap_hex(h)
        us, r = g.play.strip()
        self.assertEqual({u.id for u in us},
                         {u.id for u in g.play.stack_at(h)})
        g.frame()
        x, y, w, hh = r
        last = us[-1]
        g.tap(x + 4 + (len(us) - 1) * g.play.STRIP_STEP + 3, y + hh // 2)
        self.assertEqual(g.play.sel, [last.id])
        self.assertEqual([u.id for u in g.play.strip()[0]],
                         [u.id for u in us])       # the order holds

    def test_save_and_load(self):
        g = self.g
        g.key('e')
        g.save()
        turn, side, phase = g.e.turn, g.e.side, g.e.phase
        g2 = util.new_game(GD, side=self.side)
        g2.save_path = g.save_path
        self.assertTrue(g2.load())
        self.assertEqual((g2.e.turn, g2.e.side, g2.e.phase),
                         (turn, side, phase))
        self.assertEqual({u.id: u.hex for u in g2.e.units.values()},
                         {u.id: u.hex for u in g.e.units.values()})


class Fuzz(unittest.TestCase):
    def test_fuzz(self):
        """Random keys and taps, wide and upright, never crash."""
        keys = ['up', 'down', 'left', 'right', 'enter', 'space', 'esc', 'n',
                'u', 'e', 'a', 's', 'tab', '+', '-', '?', 'l', 't', 'g', 'p',
                'c', 'k']
        for run in range(FUZZ):
            rng = random.Random(run)
            g = util.new_game(GD, side=rng.choice(
                [None] + [s['id'] for s in GD.SIDES]), seed=run)
            for step in range(400):
                r = rng.random()
                if r < 0.45:
                    g.tap(rng.randrange(g.layout.W),
                          rng.randrange(g.layout.H))
                elif r < 0.85:
                    k = rng.choice(keys)
                    if k == 'esc' and isinstance(g.mode, TitleMode):
                        continue
                    g.key(k)
                elif r < 0.9:
                    g.portrait = not g.portrait
                else:
                    g.update(0.5)
                if g.quit:
                    break
                if step % 25 == 0:
                    g.frame()
            g.frame()


if __name__ == '__main__':
    unittest.main()
