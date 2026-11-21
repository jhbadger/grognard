"""The map on screen: which part of the painted map shows, at which zoom,
and everything drawn over it each frame (units, highlights, markers and
animations)."""

from .gfx import rgb, mix
from .hexgrid import neighbours
from . import counters
from .render import MapArt, ZOOMS, hex_tint, hex_outline, thick_line


class MapView:
    def __init__(self, game):
        self.g = game
        self.zoom = getattr(game.d, 'ZOOM', 1)
        self.arts = {}
        self.cx = self.cy = 0           # map pixel at the view's top left
        self.rect = (0, 0, 100, 100)
        self.grid = True

    # ---------------------------------------------------------- the art

    def art(self, zoom=None):
        z = self.zoom if zoom is None else zoom
        a = self.arts.get(z)
        if a is None or a.grid != self.grid:
            a = self.arts[z] = MapArt(self.g.e.board, z, grid=self.grid)
            a.paint()
        return a

    @property
    def geo(self):
        return self.art().geo

    @property
    def csize(self):
        return ZOOMS[self.zoom][2]

    def set_zoom(self, z, keep=None):
        """Change zoom, keeping the hex keep (or the middle) in place."""
        z = max(0, min(len(ZOOMS) - 1, z))
        if z == self.zoom:
            return
        x, y, w, h = self.rect
        if keep is None:
            keep = self.at(x + w // 2, y + h // 2)
        self.zoom = z
        self.center_on(keep)

    # ------------------------------------------------------- the camera

    def set_rect(self, rect):
        self.rect = rect
        self.clamp()

    def clamp(self):
        a = self.art()
        x, y, w, h = self.rect
        self.cx = max(0, min(self.cx, a.w - w)) if a.w > w else \
            -(w - a.w) // 2
        self.cy = max(0, min(self.cy, a.h - h)) if a.h > h else \
            -(h - a.h) // 2

    def center_on(self, hx):
        if hx is None:
            return
        px, py = self.geo.center(hx)
        x, y, w, h = self.rect
        self.cx, self.cy = px - w // 2, py - h // 2
        self.clamp()

    def show(self, hx, margin=40):
        """Scroll just enough to bring hx well into view."""
        sx, sy = self.to_screen(hx)
        x, y, w, h = self.rect
        if not (x + margin <= sx < x + w - margin and
                y + margin <= sy < y + h - margin):
            self.center_on(hx)

    def scroll(self, dx, dy):
        self.cx += dx
        self.cy += dy
        self.clamp()

    def to_screen(self, hx):
        px, py = self.geo.center(hx)
        return px - self.cx + self.rect[0], py - self.cy + self.rect[1]

    def at(self, sx, sy):
        """The hex under screen pixel sx, sy (or None off the map)."""
        x, y, w, h = self.rect
        if not (x <= sx < x + w and y <= sy < y + h):
            return None
        hx = self.geo.at(sx - x + self.cx, sy - y + self.cy)
        return hx if self.g.e.board.on_map(hx) else None

    def inside(self, sx, sy):
        x, y, w, h = self.rect
        return x <= sx < x + w and y <= sy < y + h

    # --------------------------------------------------------- drawing

    def draw_base(self, s):
        """Copy the visible part of the painted map."""
        a = self.art()
        base = a.get()
        x, y, w, h = self.rect
        s.rect(x, y, w, h, rgb('#1c2430'))
        W3, B3 = s.w * 3, base.w * 3
        sx0 = max(0, self.cx)
        sx1 = min(base.w, self.cx + w)
        if sx1 <= sx0:
            return
        dx = x + (sx0 - self.cx)
        n = (sx1 - sx0) * 3
        for j in range(h):
            my = self.cy + j
            if 0 <= my < base.h:
                o = (y + j) * W3 + dx * 3
                b = my * B3 + sx0 * 3
                s.buf[o:o + n] = base.buf[b:b + n]

    def restore(self, s, hx):
        """Copy one hex back from the painted map (after darkening the
        rest)."""
        base = self.art().get()
        g = self.geo
        cx, cy = g.center(hx)
        x, y, w, h = self.rect
        W3, B3 = s.w * 3, base.w * 3
        for (yy, x0, n) in g.runs:
            my = cy + yy
            sy = my - self.cy + y
            if sy < y or sy >= y + h or my < 0 or my >= base.h:
                continue
            mx0, mx1 = cx + x0, cx + x0 + n
            sx0 = max(mx0 - self.cx + x, x)
            sx1 = min(mx1 - self.cx + x, x + w)
            if sx1 <= sx0:
                continue
            m0 = sx0 - x + self.cx
            if m0 < 0 or m0 + (sx1 - sx0) > base.w:
                continue
            o = sy * W3 + sx0 * 3
            b = my * B3 + m0 * 3
            s.buf[o:o + (sx1 - sx0) * 3] = base.buf[b:b + (sx1 - sx0) * 3]

    def clip(self):
        x, y, w, h = self.rect
        return (x, y, x + w, y + h)

    def visible_hexes(self):
        x, y, w, h = self.rect
        g = self.geo
        out = []
        for hx in self.g.e.board.hexes:
            px, py = g.center(hx)
            sx, sy = px - self.cx + x, py - self.cy + y
            if x - g.dx <= sx < x + w + g.dx and y - g.dy <= sy < y + h + g.dy:
                out.append(hx)
        return out

    def tint(self, s, hx, colour, amount):
        ox, oy = self.rect[0] - self.cx, self.rect[1] - self.cy
        hex_tint(s, self.geo, hx, ox, oy, colour, amount, self.clip())

    def outline(self, s, hx, colour, width=2):
        ox, oy = self.rect[0] - self.cx, self.rect[1] - self.cy
        hex_outline(s, self.geo, hx, ox, oy, colour, self.clip(), width)

    def blit(self, s, img, x, y):
        x0, y0, x1, y1 = self.clip()
        s.set_clip(x0, y0, x1 - x0, y1 - y0)
        s.blit(img, x, y)
        s.set_clip()

    def counter_at(self, s, unit, sx, sy, dim=False, flags=(), side=None):
        """Draw unit's counter centred on screen point sx, sy."""
        g = self.g
        S = self.csize
        spec = dict(side or g.e.sides[unit.side])
        if unit.spec.get('colour'):
            spec['colour'] = unit.spec['colour']
        img = counters.counter(unit, spec, S, g.style, dim=dim,
                               flags=tuple(flags))
        self.blit(s, img, sx - S // 2, sy - S // 2)

    def draw_stack(self, s, hx, units, sel=(), dims=(), ghost=False):
        """A stack of counters in a hex, the top one first in units."""
        sx, sy = self.to_screen(hx)
        S = self.csize
        n = min(len(units), 4)
        step = 2 if S < 28 else 3
        for k in range(n - 1, -1, -1):
            u = units[k]
            off = k * step
            flags = []
            if u.oos and u.side == self.g.viewer():
                flags.append('oos')
            self.counter_at(s, u, sx - step * (n - 1) // 2 + off,
                            sy - step * (n - 1) // 2 + off,
                            dim=(u.id in dims) or ghost, flags=flags)
        top = units[0]
        if top.id in sel:
            x0 = sx - step * (n - 1) // 2 - S // 2 - 1
            y0 = sy - step * (n - 1) // 2 - S // 2 - 1
            blink = self.g.clock % 0.8 < 0.55
            c = rgb('#ffffff') if blink else rgb('#ffd040')
            x0c, y0c, x1c, y1c = self.clip()
            s.set_clip(x0c, y0c, x1c - x0c, y1c - y0c)
            s.frame(x0, y0, S + 2, S + 2, c)
            s.frame(x0 - 1, y0 - 1, S + 4, S + 4, rgb('#000000'))
            s.set_clip()
        if ghost:
            self.blit(s, s.text_image('?', (255, 255, 255), (0, 0, 0)),
                      sx - 2, sy - 5)
        if len(units) > 1 and S >= 22:
            t = str(len(units))
            img = s.text_image(t, (255, 255, 255), (0, 0, 0))
            self.blit(s, img, sx + S // 2 + 1, sy - S // 2 - 4)

    def label(self, s, hx, text, occupied):
        """A place name: across the lower half of its hex, or under the
        counters when there are some."""
        from .counters import tiny_text
        sx, sy = self.to_screen(hx)
        g = self.geo
        x0c, y0c, x1c, y1c = self.clip()
        s.set_clip(x0c, y0c, x1c - x0c, y1c - y0c)
        if self.zoom == 0:
            y = sy + (6 if occupied else 3)
            tiny_text(s, sx + 1, y + 1, text, (0, 0, 0), 'center')
            tiny_text(s, sx, y, text, (255, 255, 255), 'center')
        else:
            y = sy + self.csize // 2 + 1 if occupied else \
                sy + g.dy // 2 - 11
            img = s.text_image(text, (255, 255, 240), (0, 0, 0))
            s.blit(img, sx - img.w // 2, y)
        s.set_clip()

    def flag(self, s, hx, side, vp):
        """An objective's marker: a little flag in its holder's colour."""
        sx, sy = self.to_screen(hx)
        S = self.csize
        col = rgb(self.g.e.sides[side]['colour']) if side else \
            rgb('#ffffff')
        ink = rgb('#000000')
        x = sx + S // 2 - 2
        y = sy - S // 2 - 6
        if self.zoom == 0:
            x, y = sx + 3, sy - 9
        x0c, y0c, x1c, y1c = self.clip()
        s.set_clip(x0c, y0c, x1c - x0c, y1c - y0c)
        s.rect(x, y, 1, 10, ink)
        s.rect(x + 1, y, 7, 5, ink)
        s.rect(x + 1, y + 1, 6, 3, col)
        if self.g.e.board.objectives[hx].get('vp', 0) >= 5:
            s.rect(x + 3, y + 2, 2, 1, rgb('#c01010'))
        s.set_clip()

    def scroll_line(self, s, a, b, colour, width=2):
        """A line from hex a to hex b (attack arrows and the like)."""
        x0, y0 = self.to_screen(a)
        x1, y1 = self.to_screen(b)
        x0c, y0c, x1c, y1c = self.clip()
        s.set_clip(x0c, y0c, x1c - x0c, y1c - y0c)
        thick_line(s, x0, y0, x0 + (x1 - x0) * 0.7, y0 + (y1 - y0) * 0.7,
                   width, colour)
        s.set_clip()


def ring_colour(c, f):
    return mix(c, '#ffffff', f)


__all__ = ['MapView', 'neighbours', 'ring_colour']
