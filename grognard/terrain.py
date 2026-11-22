"""Terrain: what each kind of hex costs to enter, what it does in a fight,
and how it looks.

A game changes or adds terrain with a TERRAIN dict, each entry merged
over the stock one of that name (or over 'clear' for a new name):

    name      what the info panel calls it
    colour    the ground colour, and pattern, how it's drawn (see PATTERNS)
    ink       a second colour the pattern uses (trees, roofs, waves)
    edge      the colour of the line where it meets other terrain
    z         which terrain's edge wins where two meet
    move      cost to enter, by movement class ('foot', 'track', 'wheel'
              and any a game adds); None for can't
    shift     column shift on the combat table for a defender here
              (negative helps the defender)
    open      True where armour gets its bonus attacking into it
    los       False if it blocks line of sight (woods, towns)
    stand     True where defenders told to retreat lose a step and stay
              instead (cities)
    stack     how many units may stack here, if not the game's STACK
    impassable  True for sea and lakes (no unit may enter)

Patterns are drawn in code into a small tile that repeats, so a forest of
many hexes looks like one forest.  New ones are added with
@pattern('name').
"""

import math

from .gfx import rgb, mix, scale

TERRAIN = {
    'clear':  dict(name='Clear', colour='#9cbf68', ink='#7fa452',
                   pattern='grass', edge='#6e8f45', z=0,
                   move={'foot': 1, 'track': 1, 'wheel': 1}, shift=0,
                   open=True, los=True),
    'fields': dict(name='Fields', colour='#b4c46e', ink='#98ab58',
                   pattern='fields', edge='#7a8a40', z=1,
                   move={'foot': 1, 'track': 1, 'wheel': 2}, shift=0,
                   open=True, los=True),
    'woods':  dict(name='Woods', colour='#4e7a34', ink='#2f5420',
                   pattern='trees', edge='#1f3a14', z=5,
                   move={'foot': 2, 'track': 3, 'wheel': 4}, shift=-1,
                   open=False, los=False),
    'forest': dict(name='Forest', colour='#2f5a26', ink='#1b3a16',
                   pattern='pines', edge='#102a0c', z=6,
                   move={'foot': 2, 'track': 4, 'wheel': None}, shift=-1,
                   open=False, los=False),
    'hills':  dict(name='Hills', colour='#b9a66a', ink='#8a7446',
                   pattern='hills', edge='#6e5a30', z=3,
                   move={'foot': 2, 'track': 2, 'wheel': 3}, shift=-1,
                   open=False, los=True),
    'rough':  dict(name='Rough', colour='#a89a72', ink='#6e6248',
                   pattern='rough', edge='#5e543a', z=4,
                   move={'foot': 2, 'track': 3, 'wheel': None}, shift=-1,
                   open=False, los=True),
    'marsh':  dict(name='Marsh', colour='#7fa07a', ink='#4a7a9a',
                   pattern='marsh', edge='#3e6a6a', z=2,
                   move={'foot': 3, 'track': None, 'wheel': None}, shift=0,
                   open=False, los=True),
    'town':   dict(name='Town', colour='#b8b098', ink='#8a3a2a',
                   pattern='town', edge='#5a5048', z=7,
                   move={'foot': 1, 'track': 1, 'wheel': 1}, shift=-1,
                   open=False, los=False),
    'city':   dict(name='City', colour='#a09a8c', ink='#6a5a52',
                   pattern='city', edge='#3a342e', z=8,
                   move={'foot': 1, 'track': 2, 'wheel': 1}, shift=-2,
                   open=False, los=False, stand=True),
    'water':  dict(name='Water', colour='#3a6aa8', ink='#6a9ad0',
                   pattern='water', edge='#20406a', z=9, move={}, shift=0,
                   open=False, los=True, impassable=True),
}

# Hexside features: a game's RIVERS name one of these for each side.
#   cost    added to the cost of crossing (not along a road: bridges);
#           None for can't cross
#   halve   attacks across it are made at half strength
#   shift   a column shift when every unit attacking next to the hex does
#           so across one (a stone wall: -1, for the defender)
#   posts   drawn as a rail with posts (a fence), not a band
SIDES = {
    'stream': dict(name='Stream', colour='#4a86c8', width=1,
                   cost={'foot': 1, 'track': 1, 'wheel': 1}, halve=False),
    'river':  dict(name='River', colour='#3a74c0', width=2,
                   cost={'foot': 2, 'track': 3, 'wheel': 3}, halve=True),
    'major':  dict(name='Major river', colour='#2e64b0', width=3,
                   cost={'foot': None, 'track': None, 'wheel': None},
                   halve=True),
    'wall':   dict(name='Stone wall', colour='#a8a498', width=2,
                   cost={'foot': 1, 'track': 1, 'wheel': 2}, halve=False,
                   shift=-1),
    'fence':  dict(name='Fence', colour='#5a4024', width=1, posts=True,
                   cost={'foot': 1, 'track': 1, 'wheel': 1}, halve=False),
}

# Roads: what entering a hex along each costs, by movement class.
ROADS = {
    'road':  dict(name='Road', colour='#d8c8a0', edge='#4a3a28', width=2,
                  cost={'foot': 0.5, 'track': 0.5, 'wheel': 0.5}),
    'trail': dict(name='Trail', colour='#c8b088', edge='#6a5438', width=1,
                  cost={'foot': 1, 'track': 1, 'wheel': 1}),
    'rail':  dict(name='Railway', colour='#2a2622', edge='#2a2622',
                  width=1, cost={'foot': 1, 'track': 1, 'wheel': 1},
                  ties=True),
}


def merge(stock, changes, base='clear'):
    """stock with each entry of changes merged over it."""
    out = {k: dict(v) for k, v in stock.items()}
    for name, spec in (changes or {}).items():
        d = dict(out.get(name) or out.get(base) or {})
        d.update(spec)
        if 'move' in spec and name in stock:
            m = dict(stock[name].get('move', {}))
            m.update(spec['move'])
            d['move'] = m
        out[name] = d
    return out


# ---------------------------------------------------------------- patterns

TILE = 96
PATTERNS = {}


def pattern(name):
    def reg(fn):
        PATTERNS[name] = fn
        return fn
    return reg


def hsh(x, y, seed=0):
    """A repeatable pseudo-random number in [0, 1) for x, y."""
    n = (x * 374761393 + y * 668265263 + seed * 1442695041) & 0xffffffff
    n = ((n ^ (n >> 13)) * 1274126177) & 0xffffffff
    return ((n ^ (n >> 16)) & 0xffff) / 65536.0


def jitter_points(spacing, seed, amount=0.4):
    """Points on a jittered grid filling the tile (which repeats)."""
    pts = []
    n = max(1, TILE // spacing)
    sp = TILE / n
    for j in range(n):
        for i in range(n):
            ox = (hsh(i, j, seed) - 0.5) * sp * amount * 2
            oy = (hsh(i, j, seed + 7) - 0.5) * sp * amount * 2
            off = sp / 2 if j & 1 else 0
            pts.append(((i * sp + off + ox) % TILE, (j * sp + oy) % TILE,
                        hsh(i, j, seed + 13)))
    return pts


class Canvas:
    """A tile being painted: a TILE x TILE grid of colours that wraps."""

    def __init__(self, colour):
        self.px = [rgb(colour)] * (TILE * TILE)

    def set(self, x, y, c):
        self.px[(int(y) % TILE) * TILE + int(x) % TILE] = c

    def get(self, x, y):
        return self.px[(int(y) % TILE) * TILE + int(x) % TILE]

    def disc(self, cx, cy, r, fn):
        """Fill a disc, colouring each pixel with fn(dx, dy) (relative to
        the centre, scaled to -1..1)."""
        ir = int(r + 1)
        for y in range(-ir, ir + 1):
            for x in range(-ir, ir + 1):
                if x * x + y * y <= r * r:
                    c = fn(x / r, y / r)
                    if c is not None:
                        self.set(cx + x, cy + y, c)

    def rect(self, x, y, w, h, c):
        for yy in range(int(y), int(y + h)):
            for xx in range(int(x), int(x + w)):
                self.set(xx, yy, c)

    def speckle(self, c, amount, seed):
        c = rgb(c)
        for i in range(TILE * TILE):
            if hsh(i % TILE, i // TILE, seed) < amount:
                self.px[i] = c


@pattern('plain')
def p_plain(t, s):
    return Canvas(t['colour'])


@pattern('grass')
def p_grass(t, s):
    c = Canvas(t['colour'])
    base = rgb(t['colour'])
    c.speckle(mix(base, '#ffffff', 0.12), 0.07, 1)
    c.speckle(t['ink'], 0.08, 2)
    return c


@pattern('fields')
def p_fields(t, s):
    c = Canvas(t['colour'])
    ink = rgb(t['ink'])
    half = TILE // 2
    for y in range(TILE):
        for x in range(TILE):
            vertical = (x // half + y // half) & 1
            k = x if vertical else y
            if (k // max(2, int(3 * s))) % 2 == 0:
                c.set(x, y, ink)
    c.speckle(mix(t['colour'], '#ffffff', 0.2), 0.03, 3)
    return c


def _tree(c, x, y, r, base, ink):
    light = mix(base, '#ffffff', 0.25)

    def shade(dx, dy):
        d = dx * 0.7 + dy * 0.7
        if d > 0.35:
            return rgb(ink)
        if d < -0.45:
            return light
        return base
    c.disc(x, y, r, shade)


@pattern('trees')
def p_trees(t, s):
    c = Canvas(t['colour'])
    base = mix(t['colour'], '#ffffff', 0.08)
    ink = rgb(t['ink'])
    pts = jitter_points(max(5, int(8 * s)), 3, 0.45)
    for x, y, k in sorted(pts, key=lambda p: p[1]):
        _tree(c, x, y, (2.2 + k * 1.4) * s, base, ink)
    return c


@pattern('pines')
def p_pines(t, s):
    c = Canvas(t['colour'])
    ink = rgb(t['ink'])
    light = rgb(t.get('snow') or mix(t['colour'], '#ffffff', 0.3))
    pts = jitter_points(max(5, int(8 * s)), 5, 0.4)
    for x, y, k in sorted(pts, key=lambda p: p[1]):
        h = int((5 + 3 * k) * s)
        for j in range(h):
            half = j * 0.5 + 0.5
            for i in range(-int(half), int(half) + 1):
                col = ink if i > 0 else mix(t['colour'], '#000000', 0.15)
                if j % 3 == 0 and i <= 0 and t.get('snow'):
                    col = light
                c.set(x + i, y - h + j, col)
    return c


@pattern('hills')
def p_hills(t, s):
    c = Canvas(t['colour'])
    ink = rgb(t['ink'])
    light = mix(t['colour'], '#ffffff', 0.25)
    for x, y, k in jitter_points(max(8, int(14 * s)), 9, 0.3):
        r = (4 + 3 * k) * s
        for a in range(0, 180, 6):
            ang = math.radians(a + 180)
            px, py = x + math.cos(ang) * r, y + math.sin(ang) * r * 0.6
            c.set(px, py, ink)
            c.set(px, py - 1, light)
    c.speckle(ink, 0.03, 4)
    return c


@pattern('rough')
def p_rough(t, s):
    c = Canvas(t['colour'])
    ink = rgb(t['ink'])
    light = mix(t['colour'], '#ffffff', 0.3)
    c.speckle(ink, 0.08, 5)
    for x, y, k in jitter_points(max(6, int(10 * s)), 11, 0.5):
        r = (1.2 + k * 1.5) * s
        c.disc(x, y, r, lambda dx, dy: light if dx + dy < -0.3 else ink)
    return c


@pattern('marsh')
def p_marsh(t, s):
    c = Canvas(t['colour'])
    ink = rgb(t['ink'])
    grass = mix(t['colour'], '#000000', 0.25)
    for x, y, k in jitter_points(max(5, int(8 * s)), 13, 0.5):
        if k < 0.5:
            for i in range(int(4 * s)):
                c.set(x + i, y, ink)
        else:
            for i in range(int(3 * s)):
                c.set(x, y - i, grass)
                c.set(x - i * 0.6, y - i, grass)
                c.set(x + i * 0.6, y - i, grass)
    return c


@pattern('water')
def p_water(t, s):
    c = Canvas(t['colour'])
    ink = rgb(t['ink'])
    for x, y, k in jitter_points(max(6, int(10 * s)), 17, 0.5):
        w = int((3 + 3 * k) * s)
        for i in range(w):
            c.set(x + i, y + (1 if 0 < i < w - 1 else 0), ink)
    return c


def _buildings(t, s, spacing, seed, size):
    c = Canvas(t['colour'])
    roof = rgb(t['ink'])
    roof2 = mix(roof, '#404040', 0.4)
    wall = mix(t['colour'], '#ffffff', 0.35)
    shadow = mix(t['colour'], '#000000', 0.35)
    street = mix(t['colour'], '#000000', 0.12)
    c.speckle(street, 0.1, seed)
    for x, y, k in jitter_points(max(4, int(spacing * s)), seed, 0.25):
        w = int((size + 2 * k) * s)
        h = int((size - 1 + 2 * hsh(int(x), int(y), seed)) * s)
        col = roof if k < 0.6 else roof2
        c.rect(x + 1, y + 1, w, h, shadow)
        c.rect(x, y, w, h, col)
        c.rect(x, y + h - 1, w, 1, wall)
    return c


@pattern('town')
def p_town(t, s):
    return _buildings(t, s, 9, 21, 3)


@pattern('city')
def p_city(t, s):
    return _buildings(t, s, 6, 23, 4)


@pattern('snow')
def p_snow(t, s):
    c = Canvas(t['colour'])
    c.speckle(t['ink'], 0.06, 31)
    c.speckle(mix(t['colour'], '#ffffff', 0.5), 0.05, 32)
    return c


_tiles = {}


def tile(name, spec, s):
    """The terrain's tile at scale s, as TILE rows of bytes, each row
    twice over so a slice starting anywhere in it can run on."""
    key = (name, s)
    t = _tiles.get(key)
    if t is None:
        fn = PATTERNS.get(spec.get('pattern', 'plain'), p_plain)
        cv = fn(spec, s)
        t = []
        for y in range(TILE):
            row = b''.join(bytes(p) for p in cv.px[y * TILE:(y + 1) * TILE])
            t.append(row + row)
        _tiles[key] = t
    return t


def swatch(spec, size=12):
    """A small picture of a terrain, for the info panel and the legend."""
    from .gfx import Image
    rows = tile('swatch:' + spec.get('name', ''), spec, 1.0)
    px = []
    for y in range(size):
        r = rows[y + 8]
        for x in range(size):
            o = (x + 8) * 3
            px.append((r[o], r[o + 1], r[o + 2]))
    return Image.from_pixels(size, size, px)


__all__ = ['TERRAIN', 'SIDES', 'ROADS', 'merge', 'tile', 'pattern', 'swatch',
           'scale']
