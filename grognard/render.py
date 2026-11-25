"""Drawing the map.

The map's picture (terrain, hex grid, rivers, roads) seldom
changes during a game, so it's painted once per zoom (and again when a
game alters a hex's terrain) into a Surface the
size of the whole map, and each frame copies the part on screen.  Place
names, units, highlights and markers go on top every frame (names move
out from under the counters).
"""

from .gfx import Surface, rgb, mix
from . import hexgrid
from .hexgrid import neighbours, neighbour
from . import terrain as _terrain
from .counters import tiny_text

# Zoom levels: (column spacing, row spacing, counter size).
ZOOMS = [(16, 18, 14), (24, 28, 22), (36, 42, 32)]

OFFMAP = rgb('#1c2430')


def thick_line(s, x0, y0, x1, y1, width, colour):
    """A line width pixels wide (square brush)."""
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), \
        int(round(y1))
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    h = width // 2
    c = rgb(colour)
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i // n
        y = y0 + (y1 - y0) * i // n
        s.rect(x - h, y - h, width, width, c)


class MapArt:
    """The painted map at one zoom."""

    def __init__(self, board, zoom, grid=True, numbers=True):
        self.board = board
        self.version = board.version    # the terrain it was painted with
        dx, dy, self.csize = ZOOMS[zoom]
        self.zoom = zoom
        self.geo = hexgrid.Geometry(dx, dy)
        self.w, self.h = self.geo.size(board.cols, board.rows)
        self.grid = grid
        self.numbers = numbers
        self.surface = None

    def scale(self):
        return self.geo.dx / 24

    def paint(self):
        b, g = self.board, self.geo
        s = Surface(self.w, self.h, OFFMAP)
        sc = self.scale()
        buf = s.buf
        W3 = self.w * 3
        # terrain
        for h, tname in b.hexes.items():
            spec = b.T[tname]
            tile = _terrain.tile(tname, spec, round(sc, 2))
            cx, cy = g.center(h)
            T = _terrain.TILE
            for (yy, x0, n) in g.runs:
                y = cy + yy
                x = cx + x0
                if y < 0 or y >= self.h or x < 0 or x + n > self.w:
                    continue
                row = tile[y % T]
                o = (x % T) * 3
                buf[y * W3 + x * 3:y * W3 + (x + n) * 3] = row[o:o + n * 3]
        # a picture in the middle of each hex of a terrain that has one
        # (a star): 'glyph', fn(surface, cx, cy, scale, hex)
        for h, tname in b.hexes.items():
            fn = b.T[tname].get('glyph')
            if fn:
                cx, cy = g.center(h)
                fn(s, cx, cy, sc, h)
        # the grid: darken the outline of every hex
        if self.grid:
            dark = bytes(int(i * 0.72) for i in range(256))
            for h in b.hexes:
                cx, cy = g.center(h)
                for (ex, ey) in g.edge:
                    x, y = cx + ex, cy + ey
                    if 0 <= x < self.w and 0 <= y < self.h:
                        o = y * W3 + x * 3
                        buf[o:o + 3] = bytes(buf[o:o + 3]).translate(dark)
        # where terrain changes, the stronger terrain's edge
        wd = 1 if sc < 1.2 else 2
        for h, tname in b.hexes.items():
            for d in (0, 1, 2):
                n = neighbour(h, d)
                other = b.hexes.get(n)
                if other is None or other == tname:
                    continue
                t1, t2 = b.T[tname], b.T[other]
                top = t1 if t1.get('z', 0) >= t2.get('z', 0) else t2
                (x0, y0), (x1, y1) = g.side_line(h, d)
                thick_line(s, x0, y0, x1, y1, wd, top.get('edge', '#000'))
        # rivers along hexsides
        for (a, bb), kind in b.rivers.items():
            spec = b.S[kind]
            d = hexgrid.direction(a, bb)
            (x0, y0), (x1, y1) = g.side_line(a, d)
            wdt = max(1, int(round(spec.get('width', 2) * sc)))
            if spec.get('posts'):
                # a fence: a rail, with posts along it
                thick_line(s, x0, y0, x1, y1, 1, spec['colour'])
                n = max(2, int(round(g.R / 4)))
                for i in range(n + 1):
                    t = i / n
                    px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                    pw = max(2, wdt + 1)
                    s.rect(int(px) - pw // 2, int(py) - pw // 2, pw, pw,
                           mix(spec['colour'], '#000000', 0.3))
                continue
            thick_line(s, x0, y0, x1, y1, wdt + 2,
                       mix(spec['colour'], '#000000', 0.45))
            thick_line(s, x0, y0, x1, y1, wdt, spec['colour'])
        for (a, bb), kind in b.rivers.items():     # light middle on top
            spec = b.S[kind]
            if spec.get('width', 2) * sc >= 2 and not spec.get('posts'):
                d = hexgrid.direction(a, bb)
                (x0, y0), (x1, y1) = g.side_line(a, d)
                thick_line(s, x0, y0, x1, y1, 1,
                           mix(spec['colour'], '#ffffff', 0.35))
        # roads and railways from centre to centre
        order = sorted(b.roads.items(), key=lambda kv: kv[1] != 'rail')
        for edge_pass in (True, False):
            for (a, bb), kind in order:
                spec = b.Rd[kind]
                (x0, y0), (x1, y1) = g.center(a), g.center(bb)
                wdt = max(1, int(round(spec.get('width', 2) * sc)))
                if edge_pass:
                    if not spec.get('ties'):
                        thick_line(s, x0, y0, x1, y1, wdt + 2, spec['edge'])
                    continue
                if spec.get('ties'):
                    thick_line(s, x0, y0, x1, y1, wdt, spec['colour'])
                    n = max(1, int(g.dy / 5))
                    ddx, ddy = x1 - x0, y1 - y0
                    ln = max(1, (ddx * ddx + ddy * ddy) ** 0.5)
                    px, py = -ddy / ln * 2, ddx / ln * 2
                    for i in range(1, n * 2):
                        t = i / (n * 2)
                        mx, my = x0 + ddx * t, y0 + ddy * t
                        thick_line(s, mx - px, my - py, mx + px, my + py, 1,
                                   spec['colour'])
                else:
                    thick_line(s, x0, y0, x1, y1, wdt, spec['colour'])
        # a town square where roads meet in a built-up hex
        for h in b.hexes:
            t = b.T[b.hexes[h]]
            if t.get('pattern') in ('town', 'city') and b.has_road(h):
                cx, cy = g.center(h)
                r = max(1, int(2 * sc))
                s.rect(cx - r, cy - r, 2 * r + 1, 2 * r + 1,
                       b.Rd['road']['colour'])
        # hex numbers
        if self.numbers and self.zoom >= 2:
            for h in b.hexes:
                cx, cy = g.center(h)
                base = rgb(b.T[b.hexes[h]]['colour'])
                ink = mix(base, '#000000', 0.45)
                tiny_text(s, cx, cy - g.dy // 2 + 2, hexgrid.hid(h), ink,
                          align='center')
        self.surface = s
        return s

    def get(self):
        return self.surface or self.paint()

    def minimap(self, w, h):
        """A small picture of the whole map (one colour a hex), as a
        Surface w x h, and the scale it was drawn at."""
        b = self.board
        s = Surface(w, h, OFFMAP)
        g = hexgrid.Geometry(16, 18)
        mw, mh = g.size(b.cols, b.rows)
        f = min(w / mw, h / mh)
        for (c, r), tname in b.hexes.items():
            cx, cy = g.center((c, r))
            col = rgb(b.T[tname]['colour'])
            x0, y0 = int((cx - 8) * f), int((cy - 9) * f)
            x1, y1 = int((cx + 8) * f) + 1, int((cy + 9) * f) + 1
            s.rect(x0, y0, max(1, x1 - x0), max(1, y1 - y0), col)
        for (a, bb), kind in b.roads.items():
            if kind == 'road':
                (x0, y0), (x1, y1) = g.center(a), g.center(bb)
                s.line(x0 * f, y0 * f, x1 * f, y1 * f, b.Rd['road']['edge'])
        for (a, bb), kind in b.rivers.items():
            d = hexgrid.direction(a, bb)
            (x0, y0), (x1, y1) = g.side_line(a, d)
            s.line(x0 * f, y0 * f, x1 * f, y1 * f, b.S[kind]['colour'])
        return s, f * 16 / self.geo.dx, g


def hex_overlay(s, geo, h, ox, oy, table, clip):
    """Pass one hex's pixels on screen through a byte table (to tint or
    darken it).  ox, oy is where the map's 0, 0 is on the screen."""
    cx, cy = geo.center(h)
    cx += ox
    cy += oy
    x0c, y0c, x1c, y1c = clip
    W3 = s.w * 3
    buf = s.buf
    for (yy, x0, n) in geo.runs:
        y = cy + yy
        if y < y0c or y >= y1c:
            continue
        a = max(cx + x0, x0c)
        e = min(cx + x0 + n, x1c)
        if a >= e:
            continue
        o = y * W3 + a * 3
        buf[o:o + (e - a) * 3] = bytes(buf[o:o + (e - a) * 3]).translate(
            table)


def tint_table(colour, amount):
    """A table that moves every byte amount of the way to colour; as
    tables work on single bytes, the colour is taken as a grey level."""
    c = rgb(colour)
    lv = sum(c) // 3
    return bytes(int(i + (lv - i) * amount) for i in range(256))


def channel_tables(colour, amount):
    c = rgb(colour)
    return [bytes(int(i + (c[k] - i) * amount) for i in range(256))
            for k in range(3)]


def hex_tint(s, geo, h, ox, oy, colour, amount, clip):
    """Tint one hex's pixels on screen towards colour."""
    tabs = channel_tables(colour, amount)
    cx, cy = geo.center(h)
    cx += ox
    cy += oy
    x0c, y0c, x1c, y1c = clip
    W3 = s.w * 3
    buf = s.buf
    for (yy, x0, n) in geo.runs:
        y = cy + yy
        if y < y0c or y >= y1c:
            continue
        a = max(cx + x0, x0c)
        e = min(cx + x0 + n, x1c)
        if a >= e:
            continue
        o = y * W3 + a * 3
        seg = buf[o:o + (e - a) * 3]
        r = bytes(seg[0::3]).translate(tabs[0])
        gg = bytes(seg[1::3]).translate(tabs[1])
        bb = bytes(seg[2::3]).translate(tabs[2])
        seg[0::3] = r
        seg[1::3] = gg
        seg[2::3] = bb
        buf[o:o + (e - a) * 3] = seg


def hex_outline(s, geo, h, ox, oy, colour, clip, width=1):
    cs = geo.corners(h)
    x0c, y0c, x1c, y1c = clip
    s.set_clip(x0c, y0c, x1c - x0c, y1c - y0c)
    for i in range(6):
        (a, b), (c, d) = cs[i], cs[(i + 1) % 6]
        thick_line(s, a + ox, b + oy, c + ox, d + oy, width, colour)
    s.set_clip()


__all__ = ['MapArt', 'ZOOMS', 'hex_overlay', 'hex_tint', 'hex_outline',
           'thick_line', 'neighbours']
