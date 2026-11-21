"""Grognard: an engine for hex-and-counter wargames in pure Python with
Tk (and Kivy, for Android).

A game is a script that defines its sides, map, units and rules (see
the sample game, crossroads) and calls grognard.run(module).  The
computer can play either side, or both.
"""

import os
import sys

__version__ = '0.1'
__all__ = ['run', 'icon', 'Painter', 'parse', 'hid', 'Widget', 'widget',
           'pattern', 'symbol', 'play_out', 'simulate', 'home_dir']


def home_dir():
    """Where saves and the sound cache go: your home folder, or, if that
    can't be written to (as in an Android app), the app's own folder."""
    import tempfile
    home = os.path.expanduser('~')
    if home != '~' and os.access(home, os.W_OK):
        return home
    for d in (os.environ.get('ANDROID_PRIVATE'), os.getcwd(),
              tempfile.gettempdir()):
        if d and os.access(d, os.W_OK):
            return d
    return home


from .hexgrid import parse, hid                         # noqa: E402,F401
from .widgets import Widget, widget                     # noqa: E402,F401
from .terrain import pattern                            # noqa: E402,F401
from .counters import symbol                            # noqa: E402,F401


# ------------------------------------------------------------------ icons

ICONS = {}


def icon(name):
    """Register a function that draws a game's icon: fn(painter, size)."""
    def reg(fn):
        ICONS[name] = fn
        return fn
    return reg


class Painter:
    """A square picture to draw an icon on, at any size."""

    def __init__(self, n):
        from .counters import Pen
        self.n = n
        self.pen = Pen(n, n)

    def fill(self, c):
        from .gfx import rgb
        self.pen.rect(0, 0, self.n, self.n, rgb(c))

    def rect(self, x, y, w, h, c):
        from .gfx import rgb
        self.pen.rect(x, y, w, h, rgb(c))

    def disc(self, cx, cy, r, c):
        from .gfx import rgb
        self.pen.oval(cx, cy, r, r, rgb(c), fill=rgb(c))

    def line(self, x0, y0, x1, y1, c, width=1):
        from .gfx import rgb
        c = rgb(c)
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        h = width / 2
        for i in range(n + 1):
            t = i / n
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            self.pen.rect(int(x - h + 0.5), int(y - h + 0.5), max(1, width),
                          max(1, width), c)

    def image(self):
        return self.pen.image()


@icon('grognard')
def default_icon(p, n):
    """A counter on a hex."""
    import math
    p.fill('#2a3a5a')
    cs = [(n / 2 + math.cos(math.radians(a)) * n * 0.48,
           n / 2 + math.sin(math.radians(a)) * n * 0.48)
          for a in range(0, 360, 60)]
    for y in range(n):
        for x in range(n):
            inside = all((cs[(i + 1) % 6][0] - cs[i][0]) * (y - cs[i][1]) -
                         (cs[(i + 1) % 6][1] - cs[i][1]) * (x - cs[i][0]) >= 0
                         for i in range(6))
            if inside:
                p.rect(x, y, 1, 1, '#9cbf68')
    c = n * 0.3
    p.rect(n / 2 - c, n / 2 - c, 2 * c, 2 * c, '#a2acb4')
    p.rect(n / 2 - c * 0.6, n / 2 - c * 0.5, c * 1.2, c * 0.8, '#ffffff')
    p.line(n / 2 - c * 0.6, n / 2 - c * 0.5, n / 2 + c * 0.6,
           n / 2 + c * 0.3, '#000000', max(1, n // 40))
    p.line(n / 2 - c * 0.6, n / 2 + c * 0.3, n / 2 + c * 0.6,
           n / 2 - c * 0.5, '#000000', max(1, n // 40))


def icon_image(gdef, n=64):
    fn = ICONS.get(getattr(gdef, 'ICON', 'grognard')) or \
        ICONS['grognard']
    p = Painter(n)
    fn(p, n)
    return p.image()


# -------------------------------------------------------------------- run

def run(gdef, argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)

    def arg(flag, default=None):
        if flag in argv:
            i = argv.index(flag)
            if i + 1 < len(argv) and not argv[i + 1].startswith('--'):
                return argv[i + 1]
        return default
    if '--build-app' in argv:
        from .build import build_app
        dest = arg('--build-app') or \
            os.path.dirname(os.path.realpath(gdef.__file__))
        print(build_app(gdef, os.path.expanduser(dest)))
        return
    if '--build-android' in argv:
        from .build import build_android
        if not arg('--build-android'):
            sys.exit('--build-android needs a folder to write the project '
                     'to')
        dest = build_android(gdef, os.path.expanduser(
            arg('--build-android')))
        print('%s: build the app with %s/build.sh (Docker), or buildozer '
              'android debug' % (dest, dest))
        return
    if '--icon-png' in argv:
        from .build import icon_png
        i = argv.index('--icon-png')
        size = int(argv[i + 1])
        out = argv[i + 2] if i + 2 < len(argv) else '%s-%d.png' % (gdef.ID,
                                                                   size)
        with open(out, 'wb') as fh:
            fh.write(icon_png(gdef, size))
        print(out)
        return
    if '--selftest' in argv:
        sys.exit(selftest(gdef))
    if '--simulate' in argv:
        n = int(arg('--simulate', '10'))
        simulate(gdef, n, skill=float(arg('--skill', '1.0')))
        return
    if '--shot' in argv:
        keys = arg('--keys', '')
        shot(gdef, arg('--shot'), [k for k in keys.split(',') if k],
             seed=int(arg('--seed', '1')), portrait='--portrait' in argv)
        return
    from .sound import Sound
    from .game import Game
    try:
        import tkinter                                  # noqa: F401
        have_tk = True
    except ImportError:
        have_tk = False
    use_kivy = '--kivy' in argv or os.environ.get('GROGNARD_UI') == 'kivy' \
        or not have_tk
    snd = Sound(gdef.ID)
    if '--mute' in argv:
        snd.on = False
    snd.prepare()
    g = Game(gdef, snd)
    if '--mute' in argv:
        snd.on = False
    try:
        if use_kivy:
            from .kivyshell import KivyShell
            KivyShell(g).run()
        else:
            from .tkshell import TkShell
            scale = arg('--scale')
            TkShell(g, float(scale) if scale else None).run()
    finally:
        snd.stop()


# ------------------------------------------------------------ headless

def play_out(gdef, seed=0, skill=1.0, turns=None, log=None):
    """Play a whole game between two computer players without a screen.
    Returns the Engine at the end."""
    from .rules import Engine
    from .ai import AI
    e = Engine(gdef, seed=seed)
    ais = {s: AI(e, s, skill=skill, seed=seed * 7 + i)
           for i, s in enumerate(e.side_ids)}
    n = 0
    while not e.over and (turns is None or e.turn <= turns):
        act = ais[e.side].next_action()
        if act[0] == 'move':
            if e.move(e.units[act[1]], act[2]) is None:
                raise RuntimeError('the computer tried an illegal move: %r'
                                   % (act,))
        elif act[0] == 'attack':
            res = e.resolve(act[1], [e.units[i] for i in act[2]],
                            [e.units[i] for i in act[3]])
            adv = ais[e.side].choose_advance(res)
            e.advance([e.units[i] for i in adv], act[1])
        else:
            e.end_phase()
        e.events = []
        n += 1
        if n > 50000:
            raise RuntimeError('the game never ended')
    if log is not None:
        log.extend(e.messages)
    return e


def simulate(gdef, runs=10, skill=1.0):
    """Play runs games, computer against computer, and report who won:
    a measure of a scenario's balance."""
    import collections
    import time
    wins = collections.Counter()
    t = time.time()
    for i in range(runs):
        e = play_out(gdef, seed=i, skill=skill)
        wins[e.winner] += 1
        print('%3d  turn %2d  %s' % (i + 1, e.turn, e.result))
    print()
    for s in [s['id'] for s in gdef.SIDES] + [None]:
        if wins[s]:
            print('%-12s %d of %d' % (s or 'draw', wins[s], runs))
    print('%.1f s a game' % ((time.time() - t) / max(1, runs)))


def shot(gdef, path, keys, seed=1, portrait=False):
    """Play a list of keys without a window and save the screen as a PNG.
    Keys are the game's own ('enter', 'n', 'up'...), or tap:X:Y,
    wait:SECONDS, new:SIDE (a new game against the computer), watch (a
    game between computers), hotseat, save:FILE (an extra picture)."""
    from .game import Game
    from .png import save_surface
    from .sound import Silent
    import tempfile
    sp = os.path.join(tempfile.mkdtemp(prefix='grognard-'), 'shot.json')
    g = Game(gdef, Silent(), save_path=sp, seed=seed)
    g.portrait = portrait
    for k in keys:
        if k.startswith('wait:'):
            t = float(k[5:])
            while t > 0:
                g.update(0.05)
                t -= 0.05
        elif k.startswith('save:'):
            save_surface(g.frame(), k[5:], 2)
        elif k.startswith('tap:'):
            _, x, y = k.split(':')
            g.tap(int(x), int(y))
        elif k.startswith('new:'):
            side = k[4:]
            g.title_choose('play:' + side)
        elif k == 'watch':
            g.title_choose('watch')
        elif k == 'hotseat':
            g.title_choose('hotseat')
        elif k == 'comma':
            g.key(',')
        else:
            g.key(k)
    save_surface(g.frame(), path, 2)
    print(path)


def selftest(gdef):
    """Check the game's map and units, draw every screen once and play a
    game between two computer players.  Returns an exit status."""
    from .game import Game
    from .rules import Engine
    from .sound import Silent
    from .hexgrid import hid as _hid
    import tempfile
    problems = []
    e = Engine(gdef, seed=1)
    b = e.board
    problems += b.problems
    for u in e.units.values():
        if u.side not in e.sides:
            problems.append('%s: no side %r' % (u.id, u.side))
        if u.kind not in e.types:
            problems.append('%s: no unit type %r' % (u.id, u.kind))
        for h in ([u.hex] if u.hex else []) + u.entry:
            if not b.on_map(h):
                problems.append('%s: %s is off the map' % (u.id, _hid(h)))
            elif b.terrain(h).get('impassable'):
                problems.append('%s: %s is impassable' % (u.id, _hid(h)))
        if u.status == 'pending' and not u.entry:
            problems.append('%s: arrives but has no "at"' % u.id)
    for h in b.objectives:
        if not b.on_map(h):
            problems.append('objective %s is off the map' % _hid(h))
    for h, t in b.labels:
        if not b.on_map(h):
            problems.append('label %r at %s is off the map' % (t, _hid(h)))
    for s, cfg in getattr(gdef, 'SUPPLY', {}).items():
        if not e.supply_sources(s)[0]:
            problems.append('side %s has no supply sources on the map' % s)
    for name in set(b.hexes.values()):
        if b.T[name].get('pattern') not in __import__(
                'grognard.terrain', fromlist=['PATTERNS']).PATTERNS:
            problems.append('terrain %s: no pattern %r' % (
                name, b.T[name].get('pattern')))
    # every screen
    g = Game(gdef, Silent(), save_path=os.path.join(
        tempfile.mkdtemp(prefix='grognard-'), 'test.json'))
    for z in range(3):
        g.view.zoom = z
        g.frame()
    g.title_choose('watch')
    g.speed = 2
    for _ in range(400):
        g.update(0.1)
        if g.e.turn > 2:
            break
    g.frame()
    g.portrait = True
    g.frame()
    # a whole game
    end = play_out(gdef, seed=3)
    print('%s: %d units, %d hexes; a computer game ended on turn %d: %s'
          % (gdef.TITLE, len(e.units), len(b.hexes), end.turn, end.result))
    for p in problems:
        print(p)
    print('%d problems' % len(problems))
    return 1 if problems else 0
