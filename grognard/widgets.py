"""The panels around the map, made of widgets.

A game lists the widgets it wants in PANELS: those on the right of the
map (a column, as in the old wargames) and those along the bottom:

    PANELS = dict(right=['date', 'weather', 'victory', 'objectives',
                         'phase', 'scroll'],
                  bottom=['unit', 'orders', 'log'])

Held upright (a phone), the right-hand widgets go in columns under the
map instead.  Each widget draws itself in whatever rectangle it's given.
A game can add its own:

    @grognard.widget('supply')
    class Supply(grognard.Widget):
        def height(self, g, w): return 20
        def draw(self, g, s, r): ...
        def tap(self, g, x, y, r): return False
"""

import math

from .gfx import rgb, mix
from . import font

WIDGETS = {}

# How the panels look; a game changes any of these with CHROME.
CHROME = dict(
    bg='#161c28', panel='#222a3c', light='#6e7a98', dark='#04060a',
    text='#ece8dc', dim='#9aa2b4', accent='#ffd25a', bar='#000000',
    bar_text='#f2f2f2', button='#4a5670', button_hi='#8a96b4',
    button_lo='#161c28', button_text='#f4f2ea', paper='#e8e2cc',
    ink='#1a1a1a', red='#c02818')


def widget(name):
    def reg(cls):
        WIDGETS[name] = cls
        cls.name = name
        return cls
    return reg


def ch(g, key):
    return rgb(g.chrome[key])


def panel(g, s, r, title=None):
    """A bevelled panel box, with an optional title strip."""
    x, y, w, h = r
    s.rect(x, y, w, h, ch(g, 'panel'))
    s.bevel(x, y, w, h, ch(g, 'light'), ch(g, 'dark'))
    if title:
        s.text(x + w // 2, y + 2, title, ch(g, 'dim'), align='center')


def fit(text, width):
    """text cut down to width pixels."""
    if font.width(text) <= width:
        return text
    while len(text) > 1 and font.width(text + '.') > width:
        text = text[:-1]
    return text + '.'


def draw_buttons(g, s, buttons, x, y, w, h=14, gap=2, cols=None):
    """Buttons [(label, value, enabled)] in rows of cols filling width w;
    returns [(x0, y0, x1, y1, value)] for hit()."""
    rects = []
    n = len(buttons)
    if not n:
        return rects
    cols = cols or n
    bw = (w - gap * (cols - 1)) // cols
    for i, b in enumerate(buttons):
        label, value = b[0], b[1]
        on = b[2] if len(b) > 2 else True
        bx = x + (i % cols) * (bw + gap)
        by = y + (i // cols) * (h + gap)
        face = ch(g, 'button') if on else mix(g.chrome['button'],
                                               g.chrome['panel'], 0.6)
        s.rect(bx, by, bw, h, face)
        s.bevel(bx, by, bw, h, ch(g, 'button_hi') if on else face,
                ch(g, 'button_lo'))
        s.text(bx + bw // 2, by + (h - 9) // 2 + 1, fit(label, bw - 4),
               ch(g, 'button_text') if on else ch(g, 'dim'), align='center')
        if on:
            rects.append((bx, by, bx + bw, by + h, value))
    return rects


def hit(rects, x, y):
    for (x0, y0, x1, y1, value) in rects:
        if x0 <= x < x1 and y0 <= y < y1:
            return value
    return None


class Widget:
    flex = False
    name = ''

    def height(self, g, w):
        return 30

    def width(self, g, h):
        return 100

    def draw(self, g, s, r):
        panel(g, s, r)

    def tap(self, g, x, y, r):
        return False


# ------------------------------------------------------------- the right

MONTHS = 'JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC'.split()


@widget('date')
class Date(Widget):
    """A desk calendar: the month, the day, and the part of the day."""

    def height(self, g, w):
        return 58

    def draw(self, g, s, r):
        x, y, w, h = r
        panel(g, s, r)
        day, part = g.e.date()
        bits = day.split()
        cx = x + w // 2
        cw = min(w - 10, 52)
        s.rect(cx - cw // 2, y + 4, cw, h - 18, rgb('#f4f0e4'))
        s.rect(cx - cw // 2, y + 4, cw, 11, ch(g, 'red'))
        if len(bits) == 3 and bits[0].isdigit():
            s.text(cx, y + 5, bits[1].upper(), (255, 255, 255),
                   align='center')
            s.text(cx, y + 17, bits[0], ch(g, 'ink'), scale=2,
                   align='center')
            s.text(cx, y + h - 12, '%s %s' % (part, bits[2]) if part
                   else bits[2], ch(g, 'text'), align='center')
        else:
            s.text(cx, y + 5, 'TURN', (255, 255, 255), align='center')
            s.text(cx, y + 17, str(g.e.turn), ch(g, 'ink'), scale=2,
                   align='center')
            s.text(cx, y + h - 12, 'of %d' % g.e.turns, ch(g, 'text'),
                   align='center')

    def tap(self, g, x, y, r):
        g.show_turn_track()
        return True


def draw_weather_icon(s, icon, cx, cy, size):
    sun = rgb('#ffd040')
    cloud = rgb('#d0d4dc')
    cloud_d = rgb('#8a909c')
    r = size // 2

    def blob(x, y, rr, c):
        for yy in range(-rr, rr + 1):
            half = int(math.sqrt(max(0, rr * rr - yy * yy)))
            s.rect(x - half, y + yy, half * 2 + 1, 1, c)
    if icon in ('sun', 'clear'):
        for k in range(8):
            a = k * math.pi / 4
            s.line(cx + math.cos(a) * r * 0.55, cy + math.sin(a) * r * 0.55,
                   cx + math.cos(a) * r * 0.95, cy + math.sin(a) * r * 0.95,
                   sun)
        blob(cx, cy, int(r * 0.45), sun)
        return
    if icon == 'fog':
        for k in range(4):
            yy = cy - r // 2 + k * (r // 3 + 1)
            off = (k % 2) * 3
            s.rect(cx - r + off, yy, 2 * r - 4, 2, cloud)
        return
    blob(cx - r // 3, cy, int(r * 0.4), cloud_d)
    blob(cx + r // 4, cy - r // 5, int(r * 0.5), cloud)
    blob(cx + r // 2, cy + 1, int(r * 0.35), cloud)
    s.rect(cx - r // 2, cy + 1, r + 2, int(r * 0.35), cloud)
    if icon == 'snow':
        for k in range(5):
            fx = cx - r // 2 + k * (r // 4 + 1)
            fy = cy + r // 2 + (k % 2) * 3
            s.rect(fx, fy, 1, 3, (255, 255, 255))
            s.rect(fx - 1, fy + 1, 3, 1, (255, 255, 255))
    elif icon == 'rain':
        for k in range(5):
            fx = cx - r // 2 + k * (r // 4 + 1)
            s.line(fx, cy + r // 2, fx - 2, cy + r // 2 + 5, rgb('#80a8ff'))


@widget('weather')
class Weather(Widget):
    def height(self, g, w):
        return 44

    def draw(self, g, s, r):
        x, y, w, h = r
        panel(g, s, r)
        wx = g.e.weather()
        sky = rgb('#3a6ab8') if wx.get('air') else rgb('#4a5464')
        s.rect(x + 4, y + 4, w - 8, h - 17, sky)
        draw_weather_icon(s, wx.get('icon', 'sun'), x + w // 2,
                          y + 4 + (h - 17) // 2, min(w - 12, h - 19))
        s.text(x + w // 2, y + h - 12, fit(wx['name'], w - 4),
               ch(g, 'text'), align='center')


@widget('victory')
class Victory(Widget):
    def height(self, g, w):
        return 14 + 11 * len(g.e.side_ids)

    def draw(self, g, s, r):
        x, y, w, h = r
        panel(g, s, r, 'Victory')
        yy = y + 13
        for sid in g.e.side_ids:
            side = g.e.sides[sid]
            s.rect(x + 5, yy + 1, 7, 7, rgb(side['colour']))
            s.frame(x + 5, yy + 1, 7, 7, (0, 0, 0))
            s.text(x + 15, yy, fit(side.get('adj', side['name'])[:3], 24),
                   ch(g, 'text'))
            s.text(x + w - 5, yy, str(g.vp(sid)), ch(g, 'accent'),
                   align='right')
            yy += 11

    def tap(self, g, x, y, r):
        g.show_score()
        return True


@widget('objectives')
class Objectives(Widget):
    flex = True

    def height(self, g, w):
        return 14 + 11 * len(g.e.board.objectives)

    def rows(self, g):
        objs = g.e.board.objectives
        return sorted(objs, key=lambda h: (-objs[h]['vp'], objs[h]['name']))

    def draw(self, g, s, r):
        x, y, w, h = r
        panel(g, s, r, 'Objectives')
        yy = y + 13
        for hx in self.rows(g):
            if yy + 10 > y + h:
                break
            o = g.e.board.objectives[hx]
            owner = g.e.control.get(hx)
            col = rgb(g.e.sides[owner]['colour']) if owner else \
                rgb('#808080')
            s.rect(x + 4, yy + 1, 6, 7, col)
            s.frame(x + 4, yy + 1, 6, 7, (0, 0, 0))
            s.text(x + 13, yy, fit(o['name'], w - 16), ch(g, 'text'))
            yy += 11

    def tap(self, g, x, y, r):
        i = (y - r[1] - 13) // 11
        rows = self.rows(g)
        if 0 <= i < len(rows):
            g.view.center_on(rows[i])
            g.dirty = True
        return True


@widget('phase')
class Phase(Widget):
    def height(self, g, w):
        return 36

    def draw(self, g, s, r):
        x, y, w, h = r
        panel(g, s, r, 'Phase')
        e = g.e
        side = e.sides[e.side]
        s.rect(x + 4, y + 12, w - 8, 11, rgb(side['colour']))
        s.text(x + w // 2, y + 13, fit(side['name'], w - 10),
               rgb(side.get('ink', '#000000')), align='center')
        label = e.phase_name()
        if e.over:
            label = 'Game over'
        elif g.thinking():
            label = 'Thinking'
        s.text(x + w // 2, y + 24, label, ch(g, 'accent'), align='center')

    def tap(self, g, x, y, r):
        g.end_phase_request()
        return True


@widget('scroll')
class Scroll(Widget):
    """A 3 x 3 pad: arrows scroll the map, the middle finds the selected
    unit (or zooms out and in)."""

    def height(self, g, w):
        return min(w, 60)

    def cells(self, r):
        x, y, w, h = r
        cw, chh = (w - 8) // 3, (h - 8) // 3
        out = []
        for j in range(3):
            for i in range(3):
                out.append((x + 4 + i * cw, y + 4 + j * chh, cw - 1, chh - 1,
                            (i - 1, j - 1)))
        return out

    def draw(self, g, s, r):
        panel(g, s, r)
        for (cx, cy, cw, chh, d) in self.cells(r):
            s.rect(cx, cy, cw, chh, ch(g, 'button'))
            s.bevel(cx, cy, cw, chh, ch(g, 'button_hi'), ch(g, 'button_lo'))
            arrow(s, cx + cw // 2, cy + chh // 2, d,
                  max(2, min(cw, chh) // 3), ch(g, 'button_text'))

    def tap(self, g, x, y, r):
        for (cx, cy, cw, chh, d) in self.cells(r):
            if cx <= x < cx + cw + 1 and cy <= y < cy + chh + 1:
                if d == (0, 0):
                    g.find_selected()
                else:
                    x0, y0, w, h = g.view.rect
                    g.view.scroll(d[0] * w // 3, d[1] * h // 3)
                g.dirty = True
                return True
        return True


def arrow(s, cx, cy, d, r, colour):
    """An arrow pointing d (dx, dy: each -1, 0 or 1) centred on cx, cy,
    r pixels from the middle to the tip; for (0, 0) a dot."""
    dx, dy = d
    if not dx and not dy:
        s.rect(cx - 1, cy - 1, 3, 3, colour)
        return
    n = math.hypot(dx, dy)
    ux, uy = dx / n, dy / n             # along the arrow
    px, py = -uy, ux                    # across it
    for i in range(-r, r + 1):          # the shaft
        s.pixel(int(round(cx + ux * i)), int(round(cy + uy * i)), colour)
    for k in range(r):                  # the head
        tx, ty = cx + ux * (r - k), cy + uy * (r - k)
        for j in range(-k, k + 1):
            s.pixel(int(round(tx + px * j * 0.8)),
                    int(round(ty + py * j * 0.8)), colour)


@widget('minimap')
class Minimap(Widget):
    def height(self, g, w):
        b = g.e.board
        return int(w * (b.rows * 18 + 9) / (b.cols * 16 + 8)) + 8

    def draw(self, g, s, r):
        x, y, w, h = r
        panel(g, s, r)
        key = (w - 6, h - 6)
        cache = getattr(g, '_minimap', None)
        if not cache or cache[0] != key:
            surf, f, geo = g.view.art(0).minimap(w - 6, h - 6)
            g._minimap = cache = (key, bytes(surf.buf), surf.w, surf.h, f,
                                  geo)
        _, data, mw, mh, f, geo = cache
        s.put(x + 3, y + 3, mw, mh, data)
        vis = g.e.visible(g.viewer())
        k = mw / max(1, g.view.art(0).w)
        for u in g.e.alive():
            if u.id not in vis:
                continue
            px, py = geo.center(u.hex)
            s.rect(x + 3 + int(px * k) - 1, y + 3 + int(py * k) - 1, 3, 3,
                   rgb(g.e.sides[u.side]['colour']))
        vx, vy, vw, vh = g.view.rect
        sc = k * g.view.art(0).w / max(1, g.view.art().w)
        s.set_clip(x + 3, y + 3, mw, mh)
        s.frame(x + 3 + int(g.view.cx * sc), y + 3 + int(g.view.cy * sc),
                max(4, int(vw * sc)), max(4, int(vh * sc)), (255, 255, 255))
        s.set_clip()

    def tap(self, g, x, y, r):
        cache = getattr(g, '_minimap', None)
        if not cache:
            return True
        _, data, mw, mh, f, geo = cache
        k = mw / max(1, g.view.art(0).w)
        hx = geo.at(int((x - r[0] - 3) / k), int((y - r[1] - 3) / k))
        if g.e.board.on_map(hx):
            g.view.center_on(hx)
            g.dirty = True
        return True


# ------------------------------------------------------------ the bottom

@widget('unit')
class UnitInfo(Widget):
    """The selected unit (as in the old games: its counter, its name,
    its formation and its numbers), or the odds of the attack being
    planned, or what's in the hex tapped."""

    def width(self, g, h):
        return 214

    def draw(self, g, s, r):
        x, y, w, h = r
        panel(g, s, r)
        play = g.play
        if play and play.target is not None:
            return self.draw_odds(g, s, r)
        u = play.selected_unit() if play else None
        if u is None:
            hx = play.cursor if play else None
            if hx is not None:
                return self.draw_hex(g, s, r, hx)
            s.text(x + 6, y + 6, 'No unit selected.', ch(g, 'dim'))
            s.text(x + 6, y + 18, 'Tap a counter to select it,',
                   ch(g, 'dim'))
            s.text(x + 6, y + 29, 'or ? for help.', ch(g, 'dim'))
            return
        e = g.e
        side = e.sides[u.side]
        spec = dict(side)
        if u.spec.get('colour'):
            spec['colour'] = u.spec['colour']
        from . import counters
        img = counters.counter(u, spec, 32, g.style)
        s.blit(img, x + 5, y + (h - 33) // 2)
        tx = x + 44
        name = u.name if u.side == g.viewer() or u.id in e.visible(
            g.viewer()) else '?'
        s.text(tx, y + 4, fit('%s  %s' % (name, u.type.get('name', '')),
                              w - 48), ch(g, 'accent'))
        s.text(tx, y + 15, fit(u.long, w - 48), ch(g, 'text'))
        s.text(tx, y + 26, fit(u.formation or side['name'], w - 48),
               ch(g, 'dim'))
        bits = ['A%d D%d' % (u.attack, u.defense)]
        if u.supports or (e.ranged and u.range > 1):
            bits.append('Rng %d' % u.range)
        if u.side == e.side and e.moving:
            bits.append('MP %s/%d' % (('%.1f' % u.mp).rstrip('0').rstrip(
                '.'), u.max_mp))
        else:
            bits.append('MP %d' % u.max_mp + ('+%d' % u.m2 if u.m2 else ''))
        bits.append('Steps %d/%d' % (u.steps, u.max_steps))
        s.text(tx, y + 37, fit('  '.join(bits), w - 48), ch(g, 'text'))
        flags = []
        if u.disabled:
            flags.append('DISABLED')
        if u.oos:
            flags.append('OUT OF SUPPLY')
        if u.attacked:
            flags.append('attacked')
        if u.fired:
            flags.append('fired')
        if flags:
            s.text(x + w - 5, y + 4, ', '.join(flags), ch(g, 'red'),
                   align='right')

    def draw_hex(self, g, s, r, hx):
        from .hexgrid import hid
        from .terrain import swatch
        x, y, w, h = r
        e = g.e
        t = e.board.terrain(hx)
        s.blit(swatch(t, 16), x + 6, y + 6)
        s.frame(x + 5, y + 5, 18, 18, (0, 0, 0))
        name = e.place(hx)
        s.text(x + 28, y + 4, fit('%s  %s' % (hid(hx), t['name'])
                                  if name == hid(hx) else
                                  '%s  %s, %s' % (hid(hx), name, t['name']),
                                  w - 32), ch(g, 'accent'))
        costs = []
        for mc, c in t.get('move', {}).items():
            costs.append('%s %s' % (mc, '-' if c is None else
                                    ('%g' % c)))
        s.text(x + 28, y + 15, fit('Move: ' + (', '.join(costs) or
                                               'impassable'), w - 32),
               ch(g, 'text'))
        sh = t.get('shift', 0)
        o = e.board.objectives.get(hx)
        if o and o.get('shift'):
            sh += o['shift']
        s.text(x + 28, y + 26, 'Defence: %s' % (
            '%+d column%s' % (sh, '' if abs(sh) == 1 else 's') if sh
            else 'no shift'), ch(g, 'text'))
        if o:
            owner = e.control.get(hx)
            s.text(x + 28, y + 37, fit('Objective, %d VP: %s' % (
                o['vp'], e.side_name(owner) if owner else 'nobody'),
                w - 32), ch(g, 'text'))

    def draw_odds(self, g, s, r):
        x, y, w, h = r
        e = g.e
        play = g.play
        o = play.planned_odds()
        if o is None:
            return
        s.text(x + 6, y + 4, 'Attack on %s' % fit(e.place(play.target), 120),
               ch(g, 'accent'))
        s.text(x + 6, y + 15, '%d to %d  ' % (o['att'], o['dfn']) +
               ('= %s' % e.columns[o['col']] if o['col'] >= 0 else '(too '
                                                                    'low)'),
               ch(g, 'text'))
        sh = ', '.join('%+d %s' % (n, why) for n, why in o['shifts'])
        if o['notes']:
            sh = (sh + ', ' if sh else '') + 'river: half'
        s.text(x + 6, y + 26, fit(sh or 'no shifts', w - 12), ch(g, 'dim'))
        if o['final'] < 0:
            s.text(x + 6, y + 37, 'Odds too low to attack.', ch(g, 'red'))
            return
        s.text(x + 6, y + 37, o['label'], ch(g, 'accent'))
        xx = x + 6 + font.width(o['label']) + 6
        res = e.outcomes(o['final'])
        cw = (w - (xx - x) - 4) // max(1, len(res))
        for i, rr in enumerate(res):
            good = rr['d'] or rr['de'] or rr['retreat']
            bad = rr['a'] or rr['ae']
            col = rgb('#80e080') if good and not bad else \
                rgb('#ff8060') if bad and not good else ch(g, 'text')
            s.text(xx + i * cw, y + 37, '%d:%s' % (i + 1, rr['text']), col)
        if o.get('backing'):
            s.text(x + w - 5, y + 4, '+guns', ch(g, 'dim'), align='right')


@widget('orders')
class Orders(Widget):
    def width(self, g, h):
        return 150

    def buttons(self, g):
        play = g.play
        if play is None:
            return []
        return play.buttons()

    def draw(self, g, s, r):
        x, y, w, h = r
        panel(g, s, r)
        bs = self.buttons(g)
        cols = 2 if len(bs) <= 4 else 3
        rows = max(1, (len(bs) + cols - 1) // cols)
        bh = min(15, (h - 6 - 2 * (rows - 1)) // rows)
        self.rects = draw_buttons(g, s, bs, x + 4, y + 4, w - 8, bh,
                                  cols=cols)

    def tap(self, g, x, y, r):
        v = hit(getattr(self, 'rects', []), x, y)
        if v is not None:
            g.sound.play('click')
            g.play.order(v)
        return True


@widget('log')
class Log(Widget):
    flex = True

    def width(self, g, h):
        return 120

    def height(self, g, w):
        return 36

    def draw(self, g, s, r):
        x, y, w, h = r
        panel(g, s, r)
        n = max(1, (h - 6) // 10)
        lines = []
        for m in g.e.messages[-12:]:
            lines += font.wrap(m, w - 10)
        lines = lines[-n:]
        yy = y + 3 + (n - len(lines)) * 10
        for i, ln in enumerate(lines):
            col = ch(g, 'text') if i == len(lines) - 1 else ch(g, 'dim')
            s.text(x + 5, yy, ln, col)
            yy += 10

    def tap(self, g, x, y, r):
        g.show_log()
        return True


# ---------------------------------------------------------------- layout

class Layout:
    """Where the menu bar, the map and each widget go, for a wide screen
    or an upright one."""

    def __init__(self, g, portrait=False):
        self.portrait = portrait
        d = getattr(g.d, 'PANELS', {})
        right = d.get('right', ['date', 'weather', 'victory', 'objectives',
                                'phase', 'scroll'])
        bottom = d.get('bottom', ['unit', 'orders', 'log'])
        self.items = []         # (widget, rect)
        if not portrait:
            self.W, self.H = 640, 480
            self.bar = (0, 0, 640, 13)
            rw = 64 if right else 0
            self.map = (3, 16, 640 - 6 - rw - (3 if right else 0), 406)
            self.column(g, right, (640 - 3 - rw, 16, rw, 461))
            self.row(g, bottom, (3, 425, self.map[2], 52))
        else:
            self.W, self.H = 360, 640
            self.bar = (0, 0, 360, 13)
            self.map = (2, 15, 356, 390)
            row = [n for n in bottom if n != 'log']
            self.row(g, row, (2, 408, 356, 52))
            y = 463
            if 'log' in bottom:
                self.items.append((WIDGETS['log'](), (2, y, 356, 34)))
                y += 37
            self.columns(g, right, (2, y, 356, self.H - y - 2))

    def make(self, name):
        cls = WIDGETS.get(name)
        if cls is None:
            raise KeyError('no widget %r' % name)
        return cls()

    def column(self, g, names, r):
        x, y, w, h = r
        ws = [self.make(n) for n in names]
        fixed = sum(wd.height(g, w) + 3 for wd in ws if not wd.flex)
        flex = [wd for wd in ws if wd.flex]
        extra = max(0, h - fixed - 3 * len(flex))
        for wd in ws:
            hh = extra // len(flex) if wd.flex else wd.height(g, w)
            if wd.flex:
                hh = min(hh, max(wd.height(g, w), 20)) if \
                    len(flex) > 1 else hh
            self.items.append((wd, (x, y, w, hh)))
            y += hh + 3

    def row(self, g, names, r):
        x, y, w, h = r
        ws = [self.make(n) for n in names]
        fixed = sum(wd.width(g, h) + 3 for wd in ws if not wd.flex)
        flex = [wd for wd in ws if wd.flex]
        extra = max(0, w - fixed + (3 if not flex else 0) - 3 * len(flex))
        for wd in ws:
            ww = extra // len(flex) if wd.flex else wd.width(g, h)
            if not flex and wd is ws[-1]:
                ww = r[0] + w - x       # the last one takes what's left
            self.items.append((wd, (x, y, ww, h)))
            x += ww + 3

    def columns(self, g, names, r):
        """Widgets in columns, upright: each column 4 widgets wide at most,
        filled top to bottom."""
        x0, y0, w, h = r
        ncol = 4 if len(names) > 3 else max(1, len(names))
        cw = (w - 3 * (ncol - 1)) // ncol
        cols = [[] for _ in range(ncol)]
        hs = [0] * ncol
        for n in names:
            wd = self.make(n)
            want = wd.height(g, cw) if not wd.flex else 60
            i = min(range(ncol), key=lambda k: hs[k])
            cols[i].append([wd, want])
            hs[i] += want + 3
        for i, col in enumerate(cols):
            x = x0 + i * (cw + 3)
            y = y0
            total = sum(wh for _, wh in col) + 3 * (len(col) - 1)
            spare = h - total
            flex = [c for c in col if c[0].flex]
            for c in col:
                if c[0].flex and spare > 0:
                    c[1] += spare // len(flex)
            for wd, wh in col:
                wh = min(wh, y0 + h - y)
                if wh > 8:
                    self.items.append((wd, (x, y, cw, wh)))
                y += wh + 3

    def widget_at(self, x, y):
        for wd, r in self.items:
            rx, ry, rw, rh = r
            if rx <= x < rx + rw and ry <= y < ry + rh:
                return wd, r
        return None, None
