"""The cardboard counters, drawn in code: the side's colours, a NATO
symbol (or, if the game asks for STYLE = 'pictures', a little picture),
the unit's size above it and its numbers below.

A counter is made once for each look it can have (side, unit, steps
left, size, dimmed) and kept.  Games can draw new symbols with
@symbol('name') and new pictures with PICTURES['name'] = rows.
"""

from .gfx import Image, rgb, mix

# A 3x5 font for the numbers on counters.
TINY = {
    '0': '###/#.#/#.#/#.#/###', '1': '.#./##./.#./.#./###',
    '2': '###/..#/###/#../###', '3': '###/..#/.##/..#/###',
    '4': '#.#/#.#/###/..#/..#', '5': '###/#../###/..#/###',
    '6': '###/#../###/#.#/###', '7': '###/..#/.#./.#./.#.',
    '8': '###/#.#/###/#.#/###', '9': '###/#.#/###/..#/###',
    '-': '.../.../###/.../...', '(': '.#/#./#./#./.#', ')': '#./.#/.#/.#/#.',
    '/': '..#/..#/.#./#../#..', '.': './././././#', ' ': '../../../../..',
    '+': '.../.#./###/.#./...', '*': '#.#/.#./#.#/.../...',
    'A': '.#./#.#/###/#.#/#.#', 'B': '##./#.#/##./#.#/##.',
    'C': '###/#../#../#../###', 'D': '##./#.#/#.#/#.#/##.',
    'E': '###/#../##./#../###', 'F': '###/#../##./#../#..',
    'G': '###/#../#.#/#.#/###', 'H': '#.#/#.#/###/#.#/#.#',
    'I': '###/.#./.#./.#./###', 'J': '..#/..#/..#/#.#/###',
    'K': '#.#/#.#/##./#.#/#.#', 'L': '#../#../#../#../###',
    'M': '#.#/###/###/#.#/#.#', 'N': '##./#.#/#.#/#.#/#.#',
    'O': '###/#.#/#.#/#.#/###', 'P': '###/#.#/###/#../#..',
    'Q': '###/#.#/#.#/###/..#', 'R': '##./#.#/##./#.#/#.#',
    'S': '###/#../###/..#/###', 'T': '###/.#./.#./.#./.#.',
    'U': '#.#/#.#/#.#/#.#/###', 'V': '#.#/#.#/#.#/#.#/.#.',
    'W': '#.#/#.#/###/###/#.#', 'X': '#.#/#.#/.#./#.#/#.#',
    'Y': '#.#/#.#/.#./.#./.#.', 'Z': '###/..#/.#./#../###',
}
TINY_ROWS = {k: v.split('/') for k, v in TINY.items()}


def tiny_width(s):
    return sum(len(TINY_ROWS.get(c, TINY_ROWS[' '])[0]) + 1
               for c in s.upper()) - 1 if s else 0


def tiny(px, w, x, y, s, colour):
    """Draw s in the 3x5 font into a pixel list w wide."""
    h = len(px) // w
    for ch in s.upper():
        rows = TINY_ROWS.get(ch, TINY_ROWS[' '])
        for j, row in enumerate(rows):
            for i, b in enumerate(row):
                if b == '#' and 0 <= x + i < w and 0 <= y + j < h:
                    px[(y + j) * w + x + i] = colour
        x += len(rows[0]) + 1


def tiny_text(surface, x, y, s, colour, align='left'):
    """Draw s in the 3x5 font straight onto a Surface."""
    w = tiny_width(s)
    if align == 'center':
        x -= w // 2
    elif align == 'right':
        x -= w
    c = rgb(colour)
    for ch in s.upper():
        rows = TINY_ROWS.get(ch, TINY_ROWS[' '])
        for j, row in enumerate(rows):
            for i, b in enumerate(row):
                if b == '#':
                    surface.pixel(x + i, y + j, c)
        x += len(rows[0]) + 1
    return w


class Pen:
    """Drawing into a list of pixels."""

    def __init__(self, w, h, fill=None):
        self.w, self.h = w, h
        self.px = [fill] * (w * h)

    def set(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y * self.w + x] = c

    def rect(self, x, y, w, h, c):
        for yy in range(int(y), int(y + h)):
            for xx in range(int(x), int(x + w)):
                self.set(xx, yy, c)

    def frame(self, x, y, w, h, c):
        for xx in range(x, x + w):
            self.set(xx, y, c)
            self.set(xx, y + h - 1, c)
        for yy in range(y, y + h):
            self.set(x, yy, c)
            self.set(x + w - 1, yy, c)

    def line(self, x0, y0, x1, y1, c):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / n
            self.set(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, c)

    def oval(self, cx, cy, rx, ry, c, fill=None):
        import math
        steps = int(4 * (rx + ry)) + 8
        if fill is not None:
            for yy in range(int(cy - ry), int(cy + ry) + 1):
                for xx in range(int(cx - rx), int(cx + rx) + 1):
                    if ((xx - cx) / max(rx, .5)) ** 2 + \
                            ((yy - cy) / max(ry, .5)) ** 2 <= 1:
                        self.set(xx, yy, fill)
        for i in range(steps):
            a = 2 * math.pi * i / steps
            self.set(cx + rx * math.cos(a), cy + ry * math.sin(a), c)

    def image(self):
        return Image.from_pixels(self.w, self.h, self.px)


# ----------------------------------------------------------- NATO symbols

SYMBOLS = {}


def symbol(name):
    def reg(fn):
        SYMBOLS[name] = fn
        return fn
    return reg


def _x(p, x, y, w, h, c):
    p.line(x, y, x + w - 1, y + h - 1, c)
    p.line(x, y + h - 1, x + w - 1, y, c)


def _oval(p, x, y, w, h, c):
    rx = max(1.5, (w - 1) / 2 - max(2, w // 5))
    ry = max(1, (h - 1) / 2 - max(1, h // 4))
    p.oval(x + (w - 1) / 2, y + (h - 1) / 2, rx, ry, c)


@symbol('infantry')
def s_infantry(p, x, y, w, h, c):
    _x(p, x, y, w, h, c)


@symbol('para')
def s_para(p, x, y, w, h, c):
    _x(p, x, y, w, h, c)
    import math
    cx = x + (w - 1) / 2
    r = max(1.5, w / 8)
    for k in (-1, 1):
        for i in range(13):
            a = math.pi * (1 + i / 12)
            p.set(cx + k * r + r * math.cos(a), y + r + r * math.sin(a), c)


@symbol('glider')
def s_glider(p, x, y, w, h, c):
    _x(p, x, y, w, h, c)
    p.line(x + w // 4, y + 1, x + w - 1 - w // 4, y + 1, c)


@symbol('mountain')
def s_mountain(p, x, y, w, h, c):
    _x(p, x, y, w, h, c)
    cx = x + (w - 1) / 2
    for j in range(max(2, h // 3)):
        p.line(cx - j, y + h - 2 - (h // 3) + j + 1, cx + j,
               y + h - 2 - (h // 3) + j + 1, c)


@symbol('motorized')
def s_motorized(p, x, y, w, h, c):
    _x(p, x, y, w, h, c)
    p.line(x + (w - 1) / 2, y, x + (w - 1) / 2, y + h - 1, c)


@symbol('armor')
def s_armor(p, x, y, w, h, c):
    _oval(p, x, y, w, h, c)


@symbol('mech')
def s_mech(p, x, y, w, h, c):
    _x(p, x, y, w, h, c)
    _oval(p, x, y, w, h, c)


@symbol('recon')
def s_recon(p, x, y, w, h, c):
    p.line(x, y + h - 1, x + w - 1, y, c)


@symbol('cavalry')
def s_cavalry(p, x, y, w, h, c):
    p.line(x, y + h - 1, x + w - 1, y, c)
    _oval(p, x, y, w, h, c)


@symbol('artillery')
def s_artillery(p, x, y, w, h, c):
    r = max(1, min(w, h) // 5)
    cx, cy = x + w // 2, y + h // 2
    for yy in range(-r, r + 1):
        for xx in range(-r, r + 1):
            if xx * xx + yy * yy <= r * r + r:
                p.set(cx + xx, cy + yy, c)


@symbol('sp_art')
def s_sp_art(p, x, y, w, h, c):
    s_artillery(p, x, y, w, h, c)
    _oval(p, x, y, w, h, c)


@symbol('rocket')
def s_rocket(p, x, y, w, h, c):
    r = max(1, min(w, h) // 6)
    for k in (-1, 1):
        p.oval(x + (w - 1) / 2 + k * (r + 1), y + (h - 1) / 2, r, r, c,
               fill=c)


@symbol('antitank')
def s_antitank(p, x, y, w, h, c):
    p.line(x, y + h - 1, x + (w - 1) / 2, y, c)
    p.line(x + w - 1, y + h - 1, x + (w - 1) / 2, y, c)


@symbol('td')
def s_td(p, x, y, w, h, c):
    s_antitank(p, x, y, w, h, c)
    _oval(p, x, y, w, h, c)


@symbol('engineer')
def s_engineer(p, x, y, w, h, c):
    t = y + h // 3
    b = y + h - 1 - h // 4
    l, r = x + w // 4, x + w - 1 - w // 4
    p.line(l, t, r, t, c)
    for xx in (l, (l + r) / 2, r):
        p.line(xx, t, xx, b, c)


@symbol('hq')
def s_hq(p, x, y, w, h, c):
    tiny(p.px, p.w, x + (w - 7) // 2, y + (h - 5) // 2, 'HQ', c)


# --------------------------------------------------------------- pictures
# Little pictures for STYLE = 'pictures': '#' is the ink, '+' the light.

PICTURES = {
    'infantry': ['....##.....', '....##.....', '...####.#..', '..#.##.#...',
                 '....##.#...', '....##.....', '...#..#....', '...#..#....'],
    'armor':    ['....####...', '...######..', '#########..', '.#########.',
                 '##########.', '#.#.#.#.#..', '.#.#.#.#...', '...........'],
    'mech':     ['...........', '.....####..', '..#########', '.##########',
                 '.##########', '.#.#..#.#..', '..#....#...', '...........'],
    'artillery': ['.........##', '.......##..', '.....##....', '...####....',
                  '..######...', '.##.##.##..', '.#..#...#..', '...........'],
    'recon':    ['...........', '...####....', '..######...', '.#########.',
                 '.#########.', '..#....#...', '...........', '...........'],
    'hq':       ['.#######...', '.#+++++#...', '.#+++++#...', '.#######...',
                 '.#.........', '.#.........', '.#.........', '###........'],
    'antitank': ['..........#', '........##.', '......##...', '....###....',
                 '...#####...', '..##...##..', '.#.....#...', '...........'],
    'para':     ['...#####...', '..#.....#..', '.#.......#.', '..#.....#..',
                 '...#.#.#...', '....###....', '.....#.....', '....#.#....'],
    'engineer': ['...........', '#.........#', '###########', '#..#...#..#',
                 '#..#...#..#', '#..#...#..#', '...........', '...........'],
}
PICTURES['glider'] = PICTURES['mountain'] = PICTURES['infantry']
PICTURES['motorized'] = PICTURES['recon']
PICTURES['td'] = PICTURES['cavalry'] = PICTURES['armor']
PICTURES['sp_art'] = PICTURES['rocket'] = PICTURES['artillery']


def picture(p, name, x, y, w, h, ink, light):
    rows = PICTURES.get(name)
    if not rows:
        return False
    ph, pw = len(rows), len(rows[0])
    for yy in range(h):
        for xx in range(w):
            ch = rows[yy * ph // h][xx * pw // w]
            if ch == '#':
                p.set(x + xx, y + yy, ink)
            elif ch == '+':
                p.set(x + xx, y + yy, light)
    return True


# ---------------------------------------------------------------- counters

_cache = {}


def colours(side):
    """A side's counter colours, filled in from its 'colour'."""
    c = rgb(side.get('colour', '#808080'))
    return dict(
        bg=c,
        ink=rgb(side.get('ink', '#000000')),
        box=rgb(side.get('box')) if side.get('box') else mix(c, '#ffffff',
                                                              0.35),
        edge=mix(c, '#000000', 0.55),
        light=mix(c, '#ffffff', 0.6),
        band=rgb(side.get('band')) if side.get('band') else
        mix(c, '#ffffff', 0.75))


def size_marks(px, w, cx, y, size, ink):
    """'XX', 'III', 'II' or 'I' as little marks over the symbol."""
    if not size:
        return
    marks = []
    for ch in size:
        marks.append(ch)
    width = sum(3 if m == 'X' else 1 for m in marks) + len(marks) - 1
    x = cx - width // 2
    for m in marks:
        if m == 'X':
            for d in range(3):
                for xx, yy in ((x + d, y + d), (x + 2 - d, y + d)):
                    if 0 <= xx < w:
                        px[(y + d) * w + xx] = ink
            x += 4
        elif m in 'I|':
            for d in range(3):
                px[(y + d) * w + x] = ink
            x += 2
        elif m == '*':
            px[(y + 1) * w + x] = ink
            x += 2


def counter(unit, side, size, style='nato', dim=False, flags=()):
    """The counter for unit, size pixels square (plus a pixel of shadow
    right and below)."""
    key = (unit.id, unit.steps, size, style, dim, tuple(flags))
    img = _cache.get(key)
    if img is not None:
        return img
    col = colours(side)
    S = size
    p = Pen(S + 1, S + 1)
    bg, ink, box = col['bg'], col['ink'], col['box']
    p.rect(1, 1, S, S, mix(bg, '#000000', 0.7))          # shadow
    p.rect(0, 0, S, S, bg)
    p.frame(0, 0, S, S, col['edge'])
    if unit.reduced:
        band = max(2, S // 8)
        p.rect(1, 1, S - 2, band, col['band'])
    sym = unit.spec.get('symbol') or unit.type.get('symbol', 'infantry')
    if S < 18:
        bw, bh = S - 6, max(4, (S - 6) * 2 // 3)
        bx, by = 3, (S - bh) // 2
        p.rect(bx, by, bw, bh, box)
        p.frame(bx, by, bw, bh, ink)
        SYMBOLS.get(sym, s_infantry)(p, bx, by, bw, bh, ink)
    else:
        big = S >= 28
        bw = S - (10 if big else 8)
        bh = max(6, bw * 3 // 5)
        bx = (S - bw) // 2
        by = 5 if not unit.reduced else max(5, S // 8 + 3)
        if big:
            by += 1
        if style == 'pictures' and sym in PICTURES:
            picture(p, sym, bx, by, bw, bh, ink, col['light'])
        else:
            p.rect(bx, by, bw, bh, box)
            p.frame(bx, by, bw, bh, ink)
            SYMBOLS.get(sym, s_infantry)(p, bx + 1, by + 1, bw - 2, bh - 2,
                                         ink)
        size_marks(p.px, p.w, S // 2, by - 4, unit.size, ink)
        vals = unit.values()
        if tiny_width(vals) > S - 2:
            vals = vals.replace('-', '')
            if tiny_width(vals) > S - 2:
                vals = '%d-%d' % (unit.attack, unit.defense)
        tiny(p.px, p.w, (S - tiny_width(vals)) // 2, S - 7, vals, ink)
        if big:
            name = unit.name.upper()
            while tiny_width(name) > S - 3 and len(name) > 1:
                name = name[:-1]
            tiny(p.px, p.w, (S - tiny_width(name)) // 2, by + bh + 1, name,
                 ink)
    for f in flags:
        if f == 'oos':                  # out of supply: a red corner
            for j in range(4):
                for i in range(4 - j):
                    p.set(S - 2 - i, 1 + j, (220, 30, 20))
    img = p.image()
    if dim:
        px = img.pixels()
        img = Image.from_pixels(img.w, img.h, [
            None if c is None else mix(c, (60, 60, 60), 0.45) for c in px])
    _cache[key] = img
    if len(_cache) > 4000:
        _cache.clear()
    return img
