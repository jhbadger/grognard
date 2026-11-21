"""Hex geometry.

The map is flat-topped hexes in columns, odd columns shifted half a hex
down ("odd-q"), as on most printed wargame maps.  A hex is a (col, row)
tuple counted from 0; on screen and in a game's script it is named the
printed way, 'CCRR' counted from 1, so (0, 0) is '0101' and (11, 9) is
'1210'.

Distances, neighbours and lines are worked out in cube coordinates.
Geometry() turns hexes into pixels at one zoom: every hex is the same
shape of whole pixels (a "stamp"), so drawing the map is copying rows.
"""

# The six directions, clockwise from north, as axial (q, r) steps.
DIRS = [(0, -1), (1, -1), (1, 0), (0, 1), (-1, 1), (-1, 0)]
DIR_NAMES = ['N', 'NE', 'SE', 'S', 'SW', 'NW']


def hid(h):
    """(col, row) -> 'CCRR'."""
    return '%02d%02d' % (h[0] + 1, h[1] + 1)


def parse(s):
    """'CCRR' (or a (col, row) tuple) -> (col, row)."""
    if isinstance(s, (tuple, list)):
        return (int(s[0]), int(s[1]))
    s = str(s)
    n = len(s) // 2
    return (int(s[:n]) - 1, int(s[n:]) - 1)


def to_axial(h):
    c, r = h
    return c, r - (c - (c & 1)) // 2


def from_axial(q, r):
    return q, r + (q - (q & 1)) // 2


def neighbour(h, d):
    q, r = to_axial(h)
    dq, dr = DIRS[d]
    return from_axial(q + dq, r + dr)


def neighbours(h):
    q, r = to_axial(h)
    return [from_axial(q + dq, r + dr) for dq, dr in DIRS]


def direction(a, b):
    """The direction (0-5) from a to its neighbour b, or None."""
    qa, ra = to_axial(a)
    qb, rb = to_axial(b)
    try:
        return DIRS.index((qb - qa, rb - ra))
    except ValueError:
        return None


def distance(a, b):
    qa, ra = to_axial(a)
    qb, rb = to_axial(b)
    dq, dr = qa - qb, ra - rb
    return (abs(dq) + abs(dr) + abs(dq + dr)) // 2


def ring(h, n):
    """The hexes exactly n away."""
    if n == 0:
        return [h]
    q, r = to_axial(h)
    dq, dr = DIRS[4]
    q, r = q + dq * n, r + dr * n
    out = []
    for d in range(6):
        for _ in range(n):
            out.append(from_axial(q, r))
            q, r = q + DIRS[d][0], r + DIRS[d][1]
    return out


def within(h, n):
    out = []
    for k in range(n + 1):
        out.extend(ring(h, k))
    return out


def _round(x, y, z):
    rx, ry, rz = round(x), round(y), round(z)
    ex, ey, ez = abs(rx - x), abs(ry - y), abs(rz - z)
    if ex > ey and ex > ez:
        rx = -ry - rz
    elif ey > ez:
        ry = -rx - rz
    return int(rx), int(ry)


def line(a, b):
    """The hexes on the straight line from a to b, both included."""
    n = distance(a, b)
    if n == 0:
        return [a]
    qa, ra = to_axial(a)
    qb, rb = to_axial(b)
    # a nudge so lines along hexsides fall consistently to one side
    qa, ra = qa + 1e-6, ra + 2e-6
    out = []
    for i in range(n + 1):
        t = i / n
        q = qa + (qb - qa) * t
        r = ra + (rb - ra) * t
        out.append(from_axial(*_round(q, r, -q - r)))
    return out


def side(a, b):
    """A hexside, as the pair of hexes it lies between (order-free)."""
    return (a, b) if a <= b else (b, a)


class Geometry:
    """Hexes as pixels at one zoom.  dx is the distance between columns
    and dy between rows (even, so a half row is a whole number)."""

    def __init__(self, dx, dy):
        self.dx, self.dy = dx, dy
        self.R = dx * 2 / 3                 # centre to side corner
        self.r0 = int(round(self.R))
        self._stamp()

    def center(self, h):
        c, r = h
        return (1 + self.r0 + c * self.dx,
                1 + self.dy // 2 + r * self.dy + (self.dy // 2) * (c & 1))

    def size(self, cols, rows):
        """Pixels needed for a map of cols x rows."""
        return ((cols - 1) * self.dx + 2 * self.r0 + 3,
                rows * self.dy + self.dy // 2 + 3)

    def _key(self, px2, py2, h):
        cx, cy = self.center(h)
        ddx, ddy = px2 - 2 * cx, py2 - 2 * cy
        return (ddx * ddx + ddy * ddy, cx, cy)

    def at(self, x, y):
        """The hex (col, row) that pixel x, y belongs to."""
        c0 = int((x - 1 - self.r0) / self.dx + 0.5)
        best = None
        px2, py2 = 2 * x + 1, 2 * y + 1
        for c in (c0 - 1, c0, c0 + 1):
            r0 = int((y - 1 - self.dy // 2 - (self.dy // 2) * (c & 1))
                     / self.dy + 0.5)
            for r in (r0 - 1, r0, r0 + 1):
                k = self._key(px2, py2, (c, r))
                if best is None or k < best[0]:
                    best = (k, (c, r))
        return best[1]

    def _stamp(self):
        """The pixels of one hex relative to its centre, as rows of runs,
        and its outline (the right and bottom edges only, so neighbours
        share one line)."""
        h = (4, 4)
        cx, cy = self.center(h)
        inside = set()
        rx, ry = self.r0 + 2, self.dy // 2 + 2
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                if self.at(x, y) == h:
                    inside.add((x - cx, y - cy))
        rows = {}
        for (x, y) in inside:
            lo, hi = rows.get(y, (x, x))
            rows[y] = (min(lo, x), max(hi, x))
        self.runs = sorted((y, lo, hi - lo + 1) for y, (lo, hi) in
                           rows.items())
        self.edge = sorted((x, y) for (x, y) in inside
                           if (x + 1, y) not in inside or
                           (x, y + 1) not in inside)
        self.inside = inside
        self.top = min(y for y, _, _ in self.runs)
        self.left = min(x for _, x, _ in self.runs)
        self.width = max(x + n for _, x, n in self.runs) - self.left
        self.height = len(self.runs)

    def corners(self, h):
        """The six corners, clockwise from the east one."""
        cx, cy = self.center(h)
        R, a, b = self.R, self.dx / 3, self.dy / 2
        return [(cx + R, cy), (cx + a, cy + b), (cx - a, cy + b),
                (cx - R, cy), (cx - a, cy - b), (cx + a, cy - b)]

    def side_line(self, h, d):
        """The ends of h's side facing direction d."""
        cs = self.corners(h)
        return cs[(4 + d) % 6], cs[(5 + d) % 6]
