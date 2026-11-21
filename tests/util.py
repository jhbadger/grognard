"""Helpers for the tests: finding and loading the games, a tiny scenario
for testing the rules, and games in progress without a window."""

import glob
import importlib.machinery
import importlib.util
import os
import sys
import tempfile
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from grognard.sound import Silent                       # noqa: E402
from grognard.game import Game, Dialog                  # noqa: E402


def games():
    """The game scripts in the repository: executable files that hand
    themselves to grognard.run()."""
    out = []
    for path in sorted(glob.glob(os.path.join(ROOT, '*'))):
        if os.path.isfile(path) and os.access(path, os.X_OK) and \
                '.' not in os.path.basename(path):
            with open(path, errors='replace') as fh:
                if 'grognard.run(' in fh.read():
                    out.append(os.path.basename(path))
    return out


_loaded = {}


def load(name):
    """A game script, loaded as a module (once)."""
    if name not in _loaded:
        loader = importlib.machinery.SourceFileLoader(
            name, os.path.join(ROOT, name))
        spec = importlib.util.spec_from_loader(name, loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        _loaded[name] = mod
    return _loaded[name]


def new_game(gd, side=None, seed=1):
    """A game in progress with no window and no sound, saving to a
    temporary file; side is the one the player has (None: both)."""
    path = os.path.join(tempfile.mkdtemp(prefix='grognard-test-'),
                        'save.json')
    g = Game(gd, Silent(), save_path=path, seed=seed)
    g.title_choose('play:' + side if side else 'hotseat')
    while isinstance(g.mode, Dialog):
        g.key('enter')
    return g


def tiny(**changes):
    """A small scenario for testing the rules.

        col  1 2 3 4 5 6 7 8
        row1 . . . . . . . .
        row2 . . f . t . . .
        row3 . . f . . . h .
        row4 . . . . . . . .
        row5 . . ~ ~ . . . .
        row6 . . . . . . . .

    A road runs along row 1; a river between columns 6 and 7 in rows 3 to
    5.  Blue ('b') starts on the left, red ('r') on the right."""
    d = types.SimpleNamespace(
        __file__=os.path.join(ROOT, 'tiny'),
        ID='tiny', TITLE='Tiny', SUBTITLE='a test',
        SIDES=[dict(id='b', name='Blue', adj='Blue', colour='#6080e0'),
               dict(id='r', name='Red', adj='Red', colour='#e06060')],
        TURNS=4, STACK=2, FOG=False,
        MAP=['........',
             '..f.t...',
             '..f...h.',
             '........',
             '..~~....',
             '........'],
        ROADS=[('road', ['0101', '0801'])],
        RIVERS=[('river', ['0603/0703', '0604/0704', '0605/0705'])],
        OBJECTIVES={'0502': dict(vp=5, owner='b')},
        SUPPLY={'b': {'from': ['W'], 'range': 6},
                'r': {'from': ['E'], 'range': 6}},
        UNITS=[
            dict(id='b1', side='b', type='infantry', a=4, d=4, m=4,
                 hex='0203'),
            dict(id='b2', side='b', type='armor', a=6, d=4, m=6,
                 hex='0204'),
            dict(id='bA', side='b', type='artillery', a=4, d=1, m=3,
                 range=3, steps=1, hex='0103'),
            dict(id='r1', side='r', type='infantry', a=4, d=4, m=4,
                 hex='0703'),
            dict(id='r2', side='r', type='infantry', a=3, d=3, m=4,
                 hex='0804'),
            dict(id='r3', side='r', type='infantry', a=3, d=3, m=4,
                 arrive=2, at='0806'),
        ])
    for k, v in changes.items():
        setattr(d, k, v)
    return d
