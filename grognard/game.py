"""The game on screen: the menu bar, the map, the panels, and the stack of
modes (title, play, dialogs, menus) that take turns handling input and
drawing.

The front ends (tkshell.py, kivyshell.py) only call Game.key(),
Game.press() / drag() / release() (or tap()), Game.update() and
Game.frame(), and show the Surface frame() returns.
"""

import json
import os
import random

from .gfx import Surface, rgb, mix
from . import font
from .rules import Engine
from .ai import ai_class
from .view import MapView
from .hexgrid import hid, parse, distance
from . import widgets
from .widgets import Layout, draw_buttons, hit, fit, ch
from . import home_dir

SPEEDS = [('Slow', 0.14, 0.55), ('Normal', 0.07, 0.22), ('Fast', 0.025,
                                                          0.03)]
SKILLS = [('Easy', 0.3), ('Normal', 1.0), ('Hard', 1.8)]


# ------------------------------------------------------------------ modes

class Mode:
    """Something that owns the input: draws itself and handles keys and
    taps.  covers says whether the play screen shows underneath."""
    covers = False

    def draw(self, g, s):
        pass

    def key(self, g, k):
        pass

    def tap(self, g, x, y):
        pass

    def update(self, g, dt):
        pass


class Dialog(Mode):
    """A box of text with buttons.  pages are shown one at a time, with
    Next and Back; buttons [(label, value)] go on the last page;
    on_choose(value) is called with the button pressed (None for Esc)."""

    def __init__(self, title, pages, buttons=None, on_choose=None,
                 width=380, draw_extra=None, extra_h=0):
        self.title = title
        self.pages = pages if isinstance(pages, list) else [pages]
        self.buttons = buttons or [('OK', 'ok')]
        self.on_choose = on_choose
        self.page = 0
        self.width = width
        self.rects = []
        self.draw_extra = draw_extra
        self.extra_h = extra_h

    def box(self, g):
        W, H = g.layout.W, g.layout.H
        w = min(self.width, W - 16)
        lines = []
        for p in self.pages[self.page].split('\n'):
            lines += font.wrap(p, w - 24) if p else ['']
        h = 30 + len(lines) * font.LINE + 28 + self.extra_h
        h = min(h, H - 20)
        return (W - w) // 2, (H - h) // 2, w, h, lines

    def draw(self, g, s):
        x, y, w, h, lines = self.box(g)
        s.rect(x + 4, y + 4, w, h, (0, 0, 0))
        s.rect(x, y, w, h, ch(g, 'panel'))
        s.bevel(x, y, w, h, ch(g, 'light'), ch(g, 'dark'), 2)
        s.rect(x + 2, y + 2, w - 4, 14, ch(g, 'bar'))
        s.text(x + w // 2, y + 4, self.title, ch(g, 'bar_text'),
               align='center')
        yy = y + 22
        for ln in lines:
            if yy > y + h - 40 - self.extra_h:
                break
            s.text(x + 12, yy, ln, ch(g, 'text'))
            yy += font.LINE
        if self.draw_extra:
            self.draw_extra(g, s, (x + 12, y + h - 26 - self.extra_h,
                                   w - 24, self.extra_h))
        bs = []
        if self.page > 0:
            bs.append(('Back', '_back'))
        if self.page < len(self.pages) - 1:
            bs.append(('Next', '_next'))
        else:
            bs += self.buttons
        bw = min(w - 16, 90 * len(bs))
        self.rects = draw_buttons(g, s, bs, x + (w - bw) // 2,
                                  y + h - 22, bw, 15)
        if len(self.pages) > 1:
            s.text(x + w - 8, y + 4, '%d/%d' % (self.page + 1,
                                                len(self.pages)),
                   ch(g, 'dim'), align='right')

    def choose(self, g, v):
        if v == '_next':
            self.page += 1
        elif v == '_back':
            self.page -= 1
        else:
            g.pop(self)
            if self.on_choose:
                self.on_choose(v)
        g.dirty = True

    def key(self, g, k):
        if k in ('enter', 'space', 'right'):
            if self.page < len(self.pages) - 1:
                self.choose(g, '_next')
            elif len(self.buttons) == 1 or k != 'right':
                self.choose(g, self.buttons[0][1])
        elif k == 'left' and self.page > 0:
            self.choose(g, '_back')
        elif k == 'esc':
            g.pop(self)
            if self.on_choose:
                self.on_choose(None)
        else:
            for label, v in self.buttons:
                if label[:1].lower() == k:
                    self.choose(g, v)
                    return

    def tap(self, g, x, y):
        v = hit(self.rects, x, y)
        if v is not None:
            g.sound.play('click')
            self.choose(g, v)


class Covering(Dialog):
    """A dialog over a blank screen (handing over in a two-player game,
    so one player doesn't see the other's units)."""
    covers = True

    def draw(self, g, s):
        s.fill(ch(g, 'bg'))
        Dialog.draw(self, g, s)


class DropMenu(Mode):
    """A menu dropped from the menu bar."""

    def __init__(self, index, x, items):
        self.index = index
        self.x = x
        self.items = items          # [(label, fn or None)]
        self.sel = None

    def rect(self, g):
        w = max(font.width(lbl) for lbl, _ in self.items) + 20
        w = max(w, 110)
        x = min(self.x, g.layout.W - w - 2)
        return x, 13, w, 4 + 12 * len(self.items)

    def draw(self, g, s):
        x, y, w, h = self.rect(g)
        s.rect(x + 3, y + 3, w, h, (0, 0, 0))
        s.rect(x, y, w, h, ch(g, 'paper'))
        s.frame(x, y, w, h, (0, 0, 0))
        for i, (label, fn) in enumerate(self.items):
            yy = y + 2 + 12 * i
            if label == '-':
                s.rect(x + 4, yy + 5, w - 8, 1, rgb('#8a8a80'))
                continue
            if i == self.sel:
                s.rect(x + 1, yy, w - 2, 12, ch(g, 'bar'))
            col = ch(g, 'bar_text') if i == self.sel else \
                ch(g, 'ink') if fn else rgb('#8a8a80')
            s.text(x + 8, yy + 1, label, col)

    def choose(self, g, i):
        label, fn = self.items[i]
        if label == '-' or not fn:
            return
        g.pop(self)
        g.sound.play('click')
        fn()
        g.dirty = True

    def key(self, g, k):
        n = len(self.items)
        if k == 'esc':
            g.pop(self)
        elif k in ('down', 'up'):
            d = 1 if k == 'down' else -1
            i = self.sel if self.sel is not None else (-1 if d > 0 else n)
            for _ in range(n):
                i = (i + d) % n
                if self.items[i][0] != '-' and self.items[i][1]:
                    break
            self.sel = i
        elif k in ('left', 'right'):
            g.pop(self)
            g.open_menu((self.index + (1 if k == 'right' else -1)) %
                        len(g.menus()))
        elif k in ('enter', 'space') and self.sel is not None:
            self.choose(g, self.sel)

    def tap(self, g, x, y):
        rx, ry, rw, rh = self.rect(g)
        if rx <= x < rx + rw and ry <= y < ry + rh:
            i = (y - ry - 2) // 12
            if 0 <= i < len(self.items):
                self.choose(g, i)
            return
        g.pop(self)
        if y < 13:
            g.tap_bar(x)


# ----------------------------------------------------------------- title

class TitleMode(Mode):
    covers = True

    def __init__(self):
        self.rects = []

    def options(self, g):
        e = g.e
        opts = []
        if g.has_save():
            opts.append(('Continue the saved game', 'continue'))
        for sid in e.order:
            opts.append(('Play the %s' % e.side_name(sid), 'play:' + sid))
        opts += [('Two players, one screen', 'hotseat'),
                 ('Watch the computer play itself', 'watch'),
                 ('How to play', 'help'), ('Quit', 'quit')]
        return opts

    def draw(self, g, s):
        W, H = g.layout.W, g.layout.H
        art = g.view.art(1)
        base = art.get()
        # the map behind, darkened, from its middle
        ox = max(0, (base.w - W) // 2)
        oy = max(0, (base.h - H) // 2)
        s.fill(ch(g, 'bg'))
        w = min(W, base.w)
        for y in range(min(H, base.h)):
            o = (oy + y) * base.w * 3 + ox * 3
            s.buf[y * W * 3:y * W * 3 + w * 3] = base.buf[o:o + w * 3]
        s.darken(0, 0, W, H, 0.45)
        # counters scattered across the title
        e = g.e
        by_side = [[u for u in e.units.values() if u.side == sid]
                   for sid in e.order]
        units = [u for grp in zip(*by_side) for u in grp][:12]
        import random as _r
        rr = _r.Random(3)
        for i, u in enumerate(units):
            side = dict(e.sides[u.side])
            if u.spec.get('colour'):
                side['colour'] = u.spec['colour']
            from . import counters
            img = counters.counter(u, side, 32, g.style)
            s.blit(img, rr.randint(10, W - 50), rr.randint(H // 2 + 60,
                                                           H - 40))
        title = g.d.TITLE
        sc = 4 if font.width(title) * 4 < W - 20 else 3 if \
            font.width(title) * 3 < W - 20 else 2
        s.text(W // 2, 34, title, ch(g, 'accent'), shadow=(0, 0, 0),
               scale=sc, align='center')
        sub = getattr(g.d, 'SUBTITLE', '')
        s.text(W // 2, 34 + 10 * sc, sub, ch(g, 'text'), shadow=(0, 0, 0),
               align='center')
        opts = self.options(g)
        bw = min(260, W - 40)
        y0 = 60 + 10 * sc
        self.rects = draw_buttons(g, s, [(t, v) for t, v in opts],
                                  (W - bw) // 2, y0, bw, 17, gap=4, cols=1)
        s.text(W // 2, H - 12, 'A Grognard wargame', ch(g, 'dim'),
               align='center')

    def key(self, g, k):
        opts = self.options(g)
        if k == 'esc':
            g.quit = True
        elif k in ('enter', 'space'):
            g.title_choose(opts[0][1])
        elif k.isdigit() and 1 <= int(k) <= len(opts):
            g.title_choose(opts[int(k) - 1][1])

    def tap(self, g, x, y):
        v = hit(self.rects, x, y)
        if v:
            g.sound.play('click')
            g.title_choose(v)


# ------------------------------------------------------------------ play

class PlayMode(Mode):
    """The game itself: the map and the panels, and what a tap means in
    each phase."""

    def __init__(self, g):
        self.g = g
        self.sel = []               # selected unit ids (a stack moves too)
        self.cursor = None          # a hex looked at
        self.reach = None
        self.target = None          # the hex an attack is planned on
        self.chosen = set()         # units joining that attack
        self.pending = None         # a won fight's result: who advances
        self.undo = []
        self.wait = 0.0             # the computer's pause between moves

    # ----------------------------------------------------------- state

    def human(self):
        g = self.g
        return g.controllers.get(g.e.side) == 'human' and not g.e.over

    def selected_unit(self):
        for uid in self.sel:
            u = self.g.e.units[uid]
            if u.alive:
                return u
        return None

    def clear(self):
        self.sel = []
        self.reach = None
        self.target = None
        self.chosen = set()

    def select(self, units):
        g = self.g
        self.sel = [u.id for u in units]
        self.reach = None
        if units and self.human() and g.e.moving and \
                all(u.side == g.e.side for u in units):
            self.reach = self.group_reach(units)
        g.dirty = True

    def group_reach(self, units):
        e = self.g.e
        rs = [e.reachable(u) for u in units]
        if not rs:
            return None
        hexes = set(rs[0])
        for r in rs[1:]:
            hexes &= set(r)
        # the whole group must fit
        out = {}
        for h in hexes:
            n = sum(x.stack for x in e.at(h, units[0].side)
                    if x not in units) + sum(u.stack for u in units)
            if n <= e.stack_at(h):
                out[h] = max(r[h][0] for r in rs)
        return out

    def stack_at(self, h, side=None):
        """The units in h the viewer can see, the selected one on top."""
        g = self.g
        e = g.e
        vis = e.visible(g.viewer())
        us = [u for u in e.at(h, side) if u.id in vis]
        us.sort(key=lambda u: (u.id not in self.sel, bool(u.type.get(
            'under')), u.supports, -u.attack - u.defense, u.id))
        return us

    # ------------------------------------------------- the stack strip

    STRIP_C = 22        # counter size in the strip
    STRIP_STEP = 26     # from one counter to the next

    def strip(self):
        """The units in the selected unit's hex, when there's more than
        one, in a steady order (so tapping through them doesn't shuffle
        them), and where the strip showing them goes: (units, rect) or
        (None, None)."""
        g = self.g
        u = self.selected_unit()
        if u is None:
            return None, None
        e = g.e
        vis = e.visible(g.viewer())
        us = [x for x in e.at(u.hex) if x.id in vis]
        if len(us) < 2:
            return None, None
        us.sort(key=lambda x: (bool(x.type.get('under')), x.supports,
                               -x.attack - x.defense, x.id))
        mx, my, mw, mh = g.view.rect
        w = 8 + len(us) * self.STRIP_STEP - (self.STRIP_STEP - self.STRIP_C)
        h = self.STRIP_C + 9
        x, y = mx + 4, my + mh - h - 4
        # not over the stack it shows
        sx, sy = g.view.to_screen(u.hex)
        if x - 20 <= sx < x + w + 20 and y - 20 <= sy < y + h + 20:
            x = mx + mw - w - 4
        return us, (x, y, w, h)

    def draw_strip(self, s):
        g = self.g
        us, r = self.strip()
        if not us:
            return
        x, y, w, h = r
        s.rect(x + 2, y + 2, w, h, (0, 0, 0))
        s.rect(x, y, w, h, ch(g, 'panel'))
        s.bevel(x, y, w, h, ch(g, 'light'), ch(g, 'dark'))
        e = g.e
        from . import counters
        for i, u in enumerate(us):
            cx = x + 4 + i * self.STRIP_STEP
            cy = y + 4
            side = dict(e.sides[u.side])
            if u.spec.get('colour'):
                side['colour'] = u.spec['colour']
            flags = []
            if u.oos and u.side == g.viewer():
                flags.append('oos')
            if u.disabled:
                flags.append('dis')
            spent = self.human() and u.side == e.side and (
                (e.moving and u.mp <= 0 < u.max_mp) or
                (e.phase == 'combat' and (u.attacked or u.fired)))
            s.blit(counters.counter(u, side, self.STRIP_C, g.style,
                                    dim=spent, flags=tuple(flags)), cx, cy)
            if u.id in self.sel:
                s.frame(cx - 2, cy - 2, self.STRIP_C + 4, self.STRIP_C + 4,
                        ch(g, 'accent'))

    def tap_strip(self, x, y):
        """A tap on the strip selects the unit tapped; True if it was on
        the strip."""
        us, r = self.strip()
        if not us:
            return False
        rx, ry, rw, rh = r
        if not (rx <= x < rx + rw and ry <= y < ry + rh):
            return False
        i = (x - rx - 4) // self.STRIP_STEP
        if 0 <= i < len(us) and \
                x - rx - 4 - i * self.STRIP_STEP < self.STRIP_C:
            self.select([us[i]])
            self.g.sound.play('select')
        return True

    # ---------------------------------------------------------- orders

    def buttons(self):
        g = self.g
        e = g.e
        if e.over:
            return [('New game', 'new'), ('Score', 'score')]
        if not self.human():
            return [('Speed: %s' % SPEEDS[g.speed][0], 'speed'),
                    ('Menu', 'menu')]
        if self.pending:
            return [('Advance', 'advance', bool(self.chosen)),
                    ('Stay', 'stay')]
        if e.moving:
            u = self.selected_unit()
            many = u is not None and len(e.at(u.hex, u.side)) > 1
            out = [('Next unit', 'next'), ('Undo', 'undo', bool(self.undo)),
                   ('Whole stack', 'stack', many and len(self.sel) < 2)]
            if u is not None and u.side == e.side:
                # the game's own orders, and building where there's a yard
                out += [(label, 'act:' + k, not why)
                        for label, k, why in e.actions(u)]
                if getattr(g.d, 'BUILDS', None) and \
                        e.phase == e.phases[0] and \
                        u.hex in e.build_sites(e.side):
                    out.append(('Build...', 'build'))
            return out + [('End turn' if e.last_phase() else 'End move',
                           'end')]
        if self.target is not None:
            o = self.planned_odds()
            return [('Attack!', 'attack', o is not None and o['final'] >= 0),
                    ('Cancel', 'cancel')]
        return [('Next target', 'nexttarget', bool(e.targets())),
                ('End turn' if e.last_phase() else 'End combat', 'end')]

    def order(self, v):
        g = self.g
        e = g.e
        if v == 'next':
            self.next_unit()
        elif v == 'undo':
            self.do_undo()
        elif v == 'stack':
            u = self.selected_unit()
            if u:
                self.select([x for x in e.at(u.hex, u.side) if x.mp > 0])
        elif v == 'end':
            g.end_phase_request()
        elif v == 'build':
            u = self.selected_unit()
            if u:
                g.push(BuildMenu(u.hex))
        elif v.startswith('act:'):
            u = self.selected_unit()
            if u and e.act(u, v[4:]):
                self.undo = []
                g.sound.play('select')
                g.after_engine()
                live = [x for x in e.at(u.hex, u.side)] if u.alive else []
                self.select([u] if u.alive else live[:1])
        elif v == 'attack':
            self.attack()
        elif v == 'cancel':
            self.target = None
            self.chosen = set()
        elif v == 'nexttarget':
            self.next_target()
        elif v == 'advance':
            self.do_advance()
        elif v == 'stay':
            self.pending = None
        elif v == 'speed':
            g.speed = (g.speed + 1) % len(SPEEDS)
            g.save_settings()
        elif v == 'menu':
            g.open_menu(0)
        elif v == 'new':
            g.to_title()
        elif v == 'score':
            g.show_score()
        g.dirty = True

    def next_unit(self):
        g = self.g
        e = g.e
        if e.moving:
            units = [u for u in e.alive(e.side) if u.mp > 0 and
                     not u.moved]
        else:
            units = [u for t in e.targets() for u in e.attackers_for(t)]
        units = sorted({u.id: u for u in units}.values(),
                       key=lambda u: (u.hex[0], u.hex[1], u.id))
        if not units:
            g.flash('Every unit has moved.' if e.moving else
                    'No attacks left to make.')
            return
        cur = self.sel[0] if self.sel else None
        ids = [u.id for u in units]
        i = (ids.index(cur) + 1) % len(ids) if cur in ids else 0
        self.select([units[i]])
        g.view.show(units[i].hex)

    def next_target(self):
        g = self.g
        ts = sorted(g.e.targets())
        if not ts:
            return
        i = (ts.index(self.target) + 1) % len(ts) if self.target in ts \
            else 0
        self.set_target(ts[i])
        g.view.show(ts[i])

    # --------------------------------------------------------- moving

    def move_to(self, h):
        g = self.g
        e = g.e
        units = [e.units[i] for i in self.sel if e.units[i].alive]
        before = e.visible(g.viewer())
        rec = dict(units=[(u.id, u.hex, u.mp, u.moved, u.started)
                          for u in units],
                   control=dict(e.control), msgs=len(e.messages))
        moved = []
        fight = None
        for u in units:
            enemy = h in e.enemy_hexes(u.side)
            e.last_overrun = None
            if e.move(u, h) is None:
                break
            moved.append(u)
            if enemy:                   # an overrun: one unit at a time
                fight = e.last_overrun
                break
        if not moved:
            g.sound.play('nope')
            return
        if fight:
            self.undo = []
            g.after_engine()
            g.show_result(fight, mine=True)
            self.select([u for u in moved if u.alive])
            return
        self.undo.append(rec)
        g.after_engine()
        after = e.visible(g.viewer())
        if set(after) - set(before):
            self.undo = []
            g.flash('Contact!')
        self.select(moved if all(u.mp > 0 for u in moved) else moved)

    def do_undo(self):
        g = self.g
        e = g.e
        if not self.undo:
            return
        rec = self.undo.pop()
        for uid, hx, mp, moved, started in rec['units']:
            u = e.units[uid]
            u.hex, u.mp, u.moved, u.started = hx, mp, moved, started
        e.control = rec['control']
        del e.messages[rec['msgs']:]
        e.changed()
        g.anims = []
        self.select([e.units[uid] for uid, *_ in rec['units']])
        g.sound.play('click')

    # -------------------------------------------------------- fighting

    def set_target(self, h):
        e = self.g.e
        self.target = h
        self.chosen = {u.id for u in e.attackers_for(h) +
                       e.supporters_for(h)}
        self.sel = []
        self.reach = None
        self.g.sound.play('select')

    def planned_odds(self):
        e = self.g.e
        if self.target is None:
            return None
        att = [u for u in e.attackers_for(self.target)
               if u.id in self.chosen]
        sup = [u for u in e.supporters_for(self.target)
               if u.id in self.chosen]
        if not att and not sup:
            return dict(att=0, dfn=1, col=-1, shifts=[], final=-1,
                        notes=[], label='-', bombard=True)
        return e.odds(self.target, att, sup)

    def attack(self):
        g = self.g
        e = g.e
        o = self.planned_odds()
        if o is None or o['final'] < 0:
            g.sound.play('nope')
            return
        att = [u for u in e.attackers_for(self.target)
               if u.id in self.chosen]
        sup = [u for u in e.supporters_for(self.target)
               if u.id in self.chosen]
        target = self.target
        self.target = None
        self.chosen = set()
        res = e.resolve(target, att, sup)
        self.undo = []
        g.after_engine()
        if res.get('advance'):
            self.pending = res
            self.chosen = set()
        g.show_result(res, mine=True)

    def do_advance(self):
        g = self.g
        e = g.e
        res = self.pending
        self.pending = None
        units = [u for u in res['advance'] if u.id in self.chosen]
        e.advance(units, res['target'])
        self.chosen = set()
        g.after_engine()

    # ----------------------------------------------------------- input

    def tap_map(self, h):
        g = self.g
        e = g.e
        if h is None:
            return
        self.cursor = h
        own = self.stack_at(h, e.side) if self.human() else []
        if self.human() and self.pending:
            ids = {u.id for u in self.pending['advance'] if u.alive}
            here = [u for u in e.at(h) if u.id in ids]
            if here:
                for u in here:
                    self.chosen ^= {u.id}
            elif h == self.pending['target'] and self.chosen:
                self.do_advance()
            return
        if self.human() and e.moving:
            if self.sel and self.reach and h in self.reach:
                self.move_to(h)
                return
            if own:
                cur = self.selected_unit()
                if cur and cur.hex == h and len(self.sel) == 1 and \
                        len(own) > 1:
                    ids = [u.id for u in own]
                    nxt = own[(ids.index(cur.id) + 1) % len(own)]
                    self.select([nxt])
                else:
                    self.select([own[0]])
                g.sound.play('select')
                return
        if self.human() and e.phase == 'combat':
            if self.target is not None:
                if h == self.target:
                    return
                avail = {u.id for u in e.attackers_for(self.target) +
                         e.supporters_for(self.target)}
                here = [u for u in e.at(h, e.side) if u.id in avail]
                if here:
                    ids = {u.id for u in here}
                    if ids & self.chosen:
                        self.chosen -= ids
                    else:
                        self.chosen |= ids
                    g.sound.play('click')
                    return
            if h in e.targets():
                self.set_target(h)
                return
            if self.target is not None and not own:
                self.target = None
                self.chosen = set()
                return
        # just looking
        anyone = self.stack_at(h)
        if anyone:
            cur = self.selected_unit()
            if cur and cur.hex == h and len(anyone) > 1:
                ids = [u.id for u in anyone]
                if cur.id in ids:
                    self.select([anyone[(ids.index(cur.id) + 1) %
                                        len(anyone)]])
                    return
            self.select([anyone[0]])
        else:
            self.clear()

    def key(self, g, k):
        e = g.e
        v = g.view
        x, y, w, h = v.rect
        if k == 'up':
            v.scroll(0, -h // 4)
        elif k == 'down':
            v.scroll(0, h // 4)
        elif k == 'left':
            v.scroll(-w // 4, 0)
        elif k == 'right':
            v.scroll(w // 4, 0)
        elif k in ('+', '='):
            g.zoom(1)
        elif k == '-':
            g.zoom(-1)
        elif k in ('?', 'f1', 'h'):
            g.show_help()
        elif k == 'esc':
            if self.target is not None or self.sel or self.pending:
                if self.pending:
                    self.pending = None
                self.clear()
            else:
                g.open_menu(0)
        elif k == 'l':
            g.show_log()
        elif k == 't':
            g.show_charts()
        elif k == 'g':
            g.toggle_grid()
        elif k == 'p':
            g.toggle_style()
        elif k == 'c':
            g.find_selected()
        elif not self.human():
            if k in ('space', 'enter'):
                g.speed = len(SPEEDS) - 1
        elif self.pending:
            if k in ('enter', 'a'):
                if self.chosen:
                    self.do_advance()
                else:
                    self.pending = None
            elif k == 's':
                self.pending = None
        elif k == 'n':
            self.order('next' if e.moving else 'nexttarget')
        elif k == 'u':
            self.do_undo()
        elif k == 'tab':
            u = self.selected_unit()
            if u:
                self.tap_map(u.hex)
        elif k in ('a',) and self.target is not None:
            self.attack()
        elif k == 'enter' and self.target is not None:
            self.attack()
        elif k in ('e', 'enter', 'space'):
            g.end_phase_request()
        elif k == 'k' and e.moving:
            self.order('stack')
        g.dirty = True

    def tap(self, g, x, y):
        if g.anims:
            g.finish_anims()
        if y < 13:
            g.tap_bar(x)
            return
        if self.tap_strip(x, y):
            g.dirty = True
            return
        if g.view.inside(x, y):
            self.tap_map(g.view.at(x, y))
            g.dirty = True
            return
        wd, r = g.layout.widget_at(x, y)
        if wd:
            wd.tap(g, x, y, r)
            g.dirty = True

    # ---------------------------------------------- the computer's turn

    def update(self, g, dt):
        e = g.e
        if e.over or g.controllers.get(e.side) != 'ai':
            return
        if g.top() is not self or g.anims_blocking():
            return
        self.wait -= dt
        if self.wait > 0:
            return
        ai = g.ai_for(e.side)
        # moves the player can't see go by without a pause
        for _ in range(40):
            act = ai.next_action()
            shown = self.perform(ai, act)
            if shown or e.over or g.controllers.get(e.side) != 'ai':
                break
        self.wait = SPEEDS[g.speed][2]
        g.dirty = True

    def perform(self, ai, act):
        """Do one of the computer's actions; True if the player sees it."""
        g = self.g
        e = g.e
        viewer = g.viewer()
        if act[0] == 'move':
            u = e.units[act[1]]
            seen = viewer is None or u.side == viewer or \
                u.id in e.visible(viewer)
            e.move(u, act[2])
            seen = seen or u.id in e.visible(viewer)
            if seen:
                self.sel = [u.id]
                self.reach = None
                g.view.show(u.hex)
            g.after_engine()
            return seen
        if act[0] in ('build', 'act'):
            if act[0] == 'build':
                u = e.build(act[1], act[2])
            else:
                u = e.units[act[1]]
                e.act(u, act[2])
            seen = viewer is None or u.side == viewer
            if seen and u.alive:
                g.view.show(u.hex)
            g.after_engine()
            return seen
        if act[0] == 'attack':
            target = act[1]
            att = [e.units[i] for i in act[2]]
            sup = [e.units[i] for i in act[3]]
            g.view.show(target)
            res = e.resolve(target, att, sup)
            adv = ai.choose_advance(res)
            if adv:
                e.advance([e.units[i] for i in adv], target)
            g.after_engine()
            g.show_result(res, mine=False)
            return True
        self.clear()
        e.end_phase()
        g.after_engine()
        return True

    # ---------------------------------------------------------- drawing

    def draw(self, g, s):
        g.draw_play(s)


# ------------------------------------------------------------ animations

class MoveAnim:
    blocking = True

    def __init__(self, uid, path, per_hex):
        self.uid, self.path, self.per = uid, path, per_hex
        self.t = 0.0

    @property
    def done(self):
        return self.t >= self.per * (len(self.path) - 1)

    def pos(self, view):
        i = min(int(self.t / self.per), len(self.path) - 2)
        f = min(1.0, (self.t - i * self.per) / self.per)
        x0, y0 = view.to_screen(self.path[i])
        x1, y1 = view.to_screen(self.path[i + 1])
        return int(x0 + (x1 - x0) * f), int(y0 + (y1 - y0) * f)


class Boom:
    blocking = True

    def __init__(self, hx, dur=0.6):
        self.hx, self.dur = hx, dur
        self.t = 0.0

    @property
    def done(self):
        return self.t >= self.dur

    def draw(self, g, s):
        sx, sy = g.view.to_screen(self.hx)
        f = self.t / self.dur
        x0, y0, x1, y1 = g.view.clip()
        s.set_clip(x0, y0, x1 - x0, y1 - y0)
        rr = random.Random(int(self.t * 20) + self.hx[0])
        for k in range(10):
            r = 2 + f * g.view.csize * 0.7
            ang = rr.random() * 6.28
            import math
            px = sx + math.cos(ang) * r * rr.random()
            py = sy + math.sin(ang) * r * rr.random()
            c = mix('#fff0a0', '#c03010', f) if k % 2 else \
                mix('#ffa020', '#404040', f)
            sz = max(1, int(4 * (1 - f)) + 1)
            s.rect(int(px), int(py), sz, sz, c)
        s.set_clip()


class Popup:
    blocking = False

    def __init__(self, hx, text, colour, dur=1.6):
        self.hx, self.text, self.colour, self.dur = hx, text, colour, dur
        self.t = 0.0

    @property
    def done(self):
        return self.t >= self.dur

    def draw(self, g, s):
        sx, sy = g.view.to_screen(self.hx)
        y = int(sy - 14 - self.t * 10)
        x0, y0, x1, y1 = g.view.clip()
        s.set_clip(x0, y0, x1 - x0, y1 - y0)
        s.text(sx, y, self.text, self.colour, shadow=(0, 0, 0),
               align='center')
        s.set_clip()


# ------------------------------------------------------------------ game

class Game:
    def __init__(self, gdef, sound, save_path=None, seed=None):
        self.d = gdef
        self.sound = sound
        self.title = gdef.TITLE
        self.chrome = dict(widgets.CHROME)
        self.chrome.update(getattr(gdef, 'CHROME', {}))
        self.e = Engine(gdef, seed=seed)
        self.rng = random.Random(seed)
        self.view = MapView(self)
        self.style = getattr(gdef, 'STYLE', 'nato')
        # text in a smooth font: the window says how to measure it (Tk and
        # Kivy can; screenshots and tests keep the bitmap font)
        self.measure = None
        self.smooth_text = True
        self.controllers = {s: 'human' for s in self.e.order}
        self.skill = 1
        self.speed = 1
        self.ais = {}
        self.memory = {}            # side -> {enemy unit id: hex last seen}
        self.portrait = False
        self.screen = None          # (W, H) the window wants, if it says
        self.layout = None
        self.dirty = True
        self.quit = False
        self.clock = 0.0
        self.anims = []
        self.banner = None          # (text, time left)
        self.home = home_dir()
        self.save_path = save_path or os.path.join(self.home,
                                                   '.%s.json' % gdef.ID)
        self.settings_path = os.path.splitext(self.save_path)[0] + \
            '-settings.json'
        self.load_settings()
        self.play = PlayMode(self)
        self.modes = [self.play, TitleMode()]
        self.relayout()

    # ----------------------------------------------------------- modes

    def top(self):
        return self.modes[-1]

    @property
    def mode(self):
        return self.modes[-1]

    def push(self, m):
        self.modes.append(m)
        self.dirty = True

    def pop(self, m=None):
        if m is None:
            if len(self.modes) > 1:
                self.modes.pop()
        elif m in self.modes:
            self.modes.remove(m)
        self.dirty = True

    def tell(self, title, text, then=None, buttons=None, **kw):
        def done(v):
            if then:
                then(v)
        self.push(Dialog(title, text, buttons, done, **kw))

    def flash(self, text, t=1.6):
        self.banner = (text, t)
        self.dirty = True

    # ------------------------------------------------------- who's who

    def viewer(self):
        """Whose eyes the map is seen through: the one human side, the side
        moving in a two-player game, or nobody (everything shows) when the
        computer plays itself."""
        humans = [s for s in self.e.order
                  if self.controllers.get(s) == 'human']
        if len(humans) == 1:
            return humans[0]
        if not humans:
            return None
        return self.e.side

    def thinking(self):
        return self.controllers.get(self.e.side) == 'ai' and not self.e.over

    def ai_for(self, side):
        ai = self.ais.get(side)
        if ai is None:
            ai = self.ais[side] = ai_class(self.d)(
                self.e, side, SKILLS[self.skill][1], seed=self.rng.random())
        ai.skill = SKILLS[self.skill][1]
        return ai

    def vp(self, side):
        fn = getattr(self.d, 'SCORE', None)
        return fn(self.e, side) if fn else self.e.vp(side)

    # ----------------------------------------------------------- start

    def title_choose(self, v):
        if v == 'continue':
            if self.load():
                self.pop()
                self.flash('Welcome back.')
            return
        if v == 'help':
            self.show_help()
            return
        if v == 'quit':
            self.quit = True
            return
        sides = self.e.order
        if v.startswith('play:'):
            me = v[5:]
            ctl = {s: ('human' if s == me else 'ai') for s in sides}
        elif v == 'hotseat':
            ctl = {s: 'human' for s in sides}
        else:
            ctl = {s: 'ai' for s in sides}
        self.new_game(ctl)

    def new_game(self, controllers):
        self.e = Engine(self.d, seed=self.rng.randrange(1 << 30))
        self.controllers = controllers
        self.ais = {}
        self.memory = {}
        for s in self.e.order:
            # each side knows where the other began (the briefing), unless
            # the game keeps that secret (BRIEFING = False)
            self.memory[s] = {u.id: u.hex for u in self.e.alive()
                              if u.side != s} if \
                getattr(self.d, 'BRIEFING', True) else {}
        self.play = PlayMode(self)
        self.modes = [self.play]
        self.anims = []
        self.e.events = []
        self.view.arts = {}
        self.relayout()
        start = getattr(self.d, 'START_HEX', None)
        v = self.viewer()
        if start:
            self.view.center_on(parse(start))
        else:
            mine = self.e.alive(v) if v else self.e.alive()
            if mine:
                c = sorted(u.hex for u in mine)[len(mine) // 2]
                self.view.center_on(c)
        intro = list(getattr(self.d, 'INTRO', []))
        if v:
            about = self.e.sides[v].get('about')
            if about:
                intro.append('You command the %s. %s' % (
                    self.e.side_name(v), about))
        if intro:
            self.tell(self.d.TITLE, intro, buttons=[('Begin', 'ok')])
        self.after_engine()
        self.dirty = True

    def to_title(self):
        if not self.e.over and self.play and self.e.turn > 1:
            self.save()
        self.modes = [self.play, TitleMode()]
        self.dirty = True

    # ----------------------------------------------------- the engine

    def after_engine(self):
        """Pick up what the engine just did: animations, sounds,
        announcements, and what each side has now seen."""
        e = self.e
        viewer = self.viewer()
        per = SPEEDS[self.speed][1]
        evs, e.events = e.events, []
        for ev in evs:
            kind = ev[0]
            if kind in ('move', 'retreat'):
                u = e.units[ev[1]]
                if viewer is None or u.side == viewer or \
                        u.id in e.visible(viewer):
                    if len(ev[2]) > 1:
                        self.anims.append(MoveAnim(u.id, ev[2], per))
                        self.sound.play('tracks' if u.move_class == 'track'
                                        else 'move')
            elif kind == 'combat':
                out = ev[2]
                self.anims.append(Boom(ev[1]))
                self.sound.play('boom' if out['odds'].get('bombard')
                                else 'gun')
                txt = out['result']['text']
                if out.get('stood'):
                    txt += ' (stood)'
                self.anims.append(Popup(ev[1], txt, rgb('#ffe060')))
            elif kind == 'die':
                if ev[2] is not None:
                    self.anims.append(Popup(ev[2], 'destroyed',
                                            rgb('#ff6040'), 2.0))
            elif kind == 'turn':
                self.play.undo = []
                self.play.clear()
                d, part = e.date()
                self.flash('%s %s: %s' % (d, part, e.side_name(ev[1])),
                           2.2)
                self.sound.play('turn')
                humans = [s for s in e.order
                          if self.controllers.get(s) == 'human']
                if len(humans) > 1 and e.fog:
                    self.push(Covering('%s %s' % (d, part), [
                        'The %s to move. Pass the screen over.' %
                        e.side_name(ev[1])], [('Ready', 'ok')]))
                self.save()
            elif kind == 'phase':
                self.play.undo = []
                self.play.clear()
                self.flash('%s: %s' % (e.side_name(e.side),
                                       e.phase_name().lower()))
            elif kind == 'capture':
                self.sound.play('select')
            elif kind == 'arrive':
                pass
            elif kind == 'build':
                u = e.units[ev[1]]
                if viewer is None or u.side == viewer:
                    self.sound.play('select')
                    self.anims.append(Popup(ev[2], 'built', rgb('#80e0ff')))
            elif kind == 'over':
                self.sound.play('bugle')
                self.save()
                self.push(Dialog('The end', [e.result], [
                    ('New game', 'new'), ('Look at the map', 'look')],
                    lambda v: self.to_title() if v == 'new' else None))
        self.remember()
        self.dirty = True

    def remember(self):
        e = self.e
        for s in e.order:
            mem = self.memory.setdefault(s, {})
            vis = e.visible(s)
            mine = [u.hex for u in e.alive(s)]
            for u in e.units.values():
                if u.side == s:
                    continue
                if not u.alive:
                    mem.pop(u.id, None)
                elif u.id in vis:
                    mem[u.id] = u.hex
                elif u.id in mem and any(distance(mem[u.id], m) <= 1
                                         for m in mine):
                    del mem[u.id]

    def end_phase_request(self):
        if not self.play.human():
            return
        e = self.e
        if self.play.pending:
            self.play.pending = None
        self.play.clear()
        e.end_phase()
        self.after_engine()

    def show_result(self, res, mine):
        """Tell the player how a fight went."""
        e = self.e
        o = res['odds']
        lines = ['%s at %s: %s.' % ('Overrun' if res.get('overrun') else
                                   'Barrage' if o.get('bombard') else
                                   'Attack', e.place(res['target']),
                                   o['label'])]
        if res.get('roll'):
            lines.append('The die rolls %d: %s.' % (res['roll'],
                                                   res['result']['text']))
        lines.append('Attacker loses %d step%s, defender %d.' % (
            res['alost'], '' if res['alost'] == 1 else 's', res['dlost']))
        if res.get('disabled'):
            lines.append('Disabled: %s.' % ', '.join(
                e.units[i].name for i in res['disabled']))
        if res.get('stood'):
            lines.append('The defenders stand fast instead of retreating.')
        if mine and self.play.pending:
            lines.append('The hex is empty: tap the units to advance into '
                         'it, then Advance (or Stay).')
            self.push(Dialog('Combat', '\n'.join(lines)))
        elif mine:
            self.push(Dialog('Combat', '\n'.join(lines)))
        else:
            self.flash(lines[0] + ' ' + (lines[1] if len(lines) > 1
                                         else ''), 2.5)

    # ------------------------------------------------------- animation

    def anims_blocking(self):
        return any(a.blocking for a in self.anims)

    def finish_anims(self):
        self.anims = [a for a in self.anims if not a.blocking]
        self.dirty = True

    def update(self, dt):
        self.clock += dt
        if self.anims:
            for a in self.anims:
                a.t += dt
            self.anims = [a for a in self.anims if not a.done]
            self.dirty = True
        if self.banner:
            t = self.banner[1] - dt
            self.banner = (self.banner[0], t) if t > 0 else None
            self.dirty = True
        for m in list(self.modes):
            m.update(self, dt)
        if self.play.sel and int((self.clock - dt) / 0.4) != \
                int(self.clock / 0.4):
            self.dirty = True

    # ----------------------------------------------------------- input

    def key(self, k):
        self.mode.key(self, k)
        self.dirty = True

    def tap(self, x, y):
        self.mode.tap(self, x, y)
        self.dirty = True

    # a press, drag and release on the map scrolls it; without the drag
    # it's a tap
    def press(self, x, y):
        self._press = (x, y, x, y, False)

    def drag(self, x, y):
        p = getattr(self, '_press', None)
        if not p:
            return
        x0, y0, lx, ly, dragging = p
        if not dragging and abs(x - x0) + abs(y - y0) > 6 and \
                self.top() is self.play and self.view.inside(x0, y0):
            dragging = True
        if dragging:
            self.view.scroll(lx - x, ly - y)
            self.dirty = True
        self._press = (x0, y0, x, y, dragging)

    def release(self, x, y):
        p = getattr(self, '_press', None)
        self._press = None
        if p and p[4]:
            return
        self.tap(x, y)

    def wheel(self, dx, dy):
        if self.top() is self.play:
            self.view.scroll(dx * 30, dy * 30)
            self.dirty = True

    # ------------------------------------------------------- menu bar

    def menus(self):
        p = self.play
        e = self.e
        human = p.human()
        return [
            ('Game', [('New game', self.to_title),
                      ('Save', self.save_now if not e.over else None),
                      ('Load saved game', self.load_now
                       if self.has_save() else None),
                      ('-', None), ('Quit', self.quit_now)]),
            ('View', [('Zoom in   +', lambda: self.zoom(1)),
                      ('Zoom out   -', lambda: self.zoom(-1)),
                      ('Hex grid   G', self.toggle_grid),
                      ('Counters: %s   P' % ('pictures' if self.style ==
                                             'pictures' else 'NATO'),
                       self.toggle_style),
                      ('Text: %s' % ('smooth' if self.smooth_text else
                                     'pixels'),
                       self.toggle_text if self.measure else None),
                      ('Find selected   C', self.find_selected)] +
             ([('Upright screen' if not self.portrait else 'Wide screen',
                self.toggle_portrait)] if self.screen is None else [])),
            ('Orders', [('End phase   E', self.end_phase_request
                         if human else None),
                        ('Next unit   N', (lambda: p.order('next'))
                         if human and e.moving else None),
                        ('Next target   N', (lambda: p.order('nexttarget'))
                         if human and e.phase == 'combat' else None),
                        ('Undo move   U', p.do_undo if p.undo else None),
                        ('-', None),
                        ('Turn record', self.show_turn_track),
                        ('Score', self.show_score),
                        ('Log   L', self.show_log)]),
            ('Options', [('Computer: %s' % SKILLS[self.skill][0],
                          self.cycle_skill),
                         ('Speed: %s' % SPEEDS[self.speed][0],
                          self.cycle_speed),
                         ('Sound: %s' % ('on' if self.sound.on else 'off'),
                          self.toggle_sound),
                         ('Sides...', self.choose_sides)]),
            ('Help', [('How to play   ?', self.show_help),
                      ('Charts   T', self.show_charts),
                      ('About %s' % self.d.TITLE, self.show_about)]),
        ]

    def bar_items(self):
        x = 6
        out = []
        for i, (name, _) in enumerate(self.menus()):
            w = font.width(name)
            out.append((x - 4, x + w + 4, i))
            x += w + 14
        return out

    def tap_bar(self, x):
        for x0, x1, i in self.bar_items():
            if x0 <= x < x1:
                self.open_menu(i)
                return

    def open_menu(self, i):
        ms = self.menus()
        if not ms:
            return
        x0 = [b[0] for b in self.bar_items()][i]
        self.push(DropMenu(i, x0, ms[i][1]))

    # ------------------------------------------------- menu commands

    def zoom(self, d):
        self.view.set_zoom(self.view.zoom + d)
        self.save_settings()
        self.dirty = True

    def toggle_grid(self):
        self.view.grid = not self.view.grid
        self.view.arts = {}
        self.save_settings()

    def toggle_text(self):
        self.smooth_text = not self.smooth_text
        self.save_settings()

    def toggle_style(self):
        self.style = 'pictures' if self.style == 'nato' else 'nato'
        self.save_settings()

    def toggle_portrait(self):
        self.portrait = not self.portrait
        self.relayout()

    def toggle_sound(self):
        self.sound.on = not self.sound.on
        self.save_settings()

    def cycle_skill(self):
        self.skill = (self.skill + 1) % len(SKILLS)
        self.save_settings()

    def cycle_speed(self):
        self.speed = (self.speed + 1) % len(SPEEDS)
        self.save_settings()

    def find_selected(self):
        u = self.play.selected_unit()
        if u:
            self.view.center_on(u.hex)
        self.dirty = True

    def quit_now(self):
        if not self.e.over:
            self.save()
        self.quit = True

    def save_now(self):
        self.save()
        self.flash('Game saved.')

    def load_now(self):
        if self.load():
            self.flash('Game loaded.')

    def choose_sides(self):
        e = self.e
        opts = [('%s: %s' % (e.side_name(s), 'computer' if
                             self.controllers[s] == 'ai' else 'player'), s)
                for s in e.order]

        def pick(v):
            if v in self.controllers:
                self.controllers[v] = 'human' if \
                    self.controllers[v] == 'ai' else 'ai'
                self.play.clear()
                self.choose_sides()
        # Done needs a value: a tap on a button worth None counts as a miss
        self.push(Dialog('Sides', 'Tap a side to switch it between you and '
                         'the computer.', opts + [('Done', '_done')], pick))

    def show_help(self):
        pages = list(HELP)
        pages += list(getattr(self.d, 'HELP', []))
        self.push(Dialog('How to play', pages, width=440))

    def show_about(self):
        pages = list(getattr(self.d, 'INTRO', [])) or [self.d.TITLE]
        self.push(Dialog(self.d.TITLE, pages, width=440))

    def show_log(self):
        lines = self.e.log(self.viewer(), 24)
        self.push(Dialog('Log', '\n'.join(lines) or 'Nothing yet.',
                         width=460))

    def show_score(self):
        e = self.e
        lines = []
        # a game that keeps the score secret (HIDDEN_SCORE) shows only
        # your own until the end
        secret = getattr(self.d, 'HIDDEN_SCORE', False) and not e.over \
            and self.viewer() is not None
        for s in e.order:
            if secret and s != self.viewer():
                continue
            lines.append('%s: %d VP' % (e.side_name(s), self.vp(s)))
        lines.append('')
        for s in e.order:
            lines.append('%s steps lost: %d' % (e.side_name(s, 'adj'),
                                                e.lost[s]))
            if e.exited.get(s):
                lines.append('%s steps exited: %d' % (e.side_name(s, 'adj'),
                                                      e.exited[s]))
        held = {}
        for h, o in e.board.objectives.items():
            held.setdefault(e.control.get(h), []).append(
                '%s (%d)' % (o['name'], o['vp']))
        for s in e.order:
            if held.get(s):
                lines.append('%s %s: %s' % (
                    e.side_name(s), e.verb(s, 'hold'), ', '.join(held[s])))
        if e.over:
            lines += ['', e.result]
        self.push(Dialog('Score', '\n'.join(lines), width=440))

    def show_turn_track(self):
        e = self.e
        lines = []
        for t in range(1, e.turns + 1):
            d, part = e.date(t)
            w = e.weather(t)['name']
            arr = [u.name for u in e.units.values() if u.arrive == t and
                   u.entry and (u.side == self.viewer() or
                                self.viewer() is None)]
            mark = '>' if t == e.turn else ' '
            lines.append('%s %2d  %s %s, %s%s' % (
                mark, t, d, part, w, ('. Arriving: ' + ', '.join(arr))
                if arr else ''))
        self.push(Dialog('Turn record', '\n'.join(lines), width=500))

    def show_charts(self):
        self.push(Charts())

    # ------------------------------------------------------- the screen

    def relayout(self):
        self.layout = Layout(self, self.portrait, self.screen)
        self.view.set_rect(self.layout.map)
        self.dirty = True

    def set_screen(self, size, portrait):
        """The window says how big a screen to draw (in the game's own
        pixels, before it scales it up) and which way up."""
        if size != self.screen or portrait != self.portrait:
            self.screen = size
            self.portrait = portrait
            self.relayout()

    def frame(self):
        L = self.layout
        if L is None or L.portrait != self.portrait or \
                (self.screen and (L.W, L.H) != self.screen):
            self.relayout()
        s = self.render()
        self.dirty = False
        return s

    def render(self):
        L = self.layout
        s = Surface(L.W, L.H, ch(self, 'bg'))
        smooth = self.smooth_text and self.measure is not None
        font.set_metrics(self.measure if smooth else None)
        if smooth:
            s.texts = []
        first = 0
        for i, m in enumerate(self.modes):
            if m.covers:
                first = i
        for m in self.modes[first:]:
            m.draw(self, s)
        return s

    def draw_bar(self, s):
        L = self.layout
        x, y, w, h = L.bar
        s.rect(x, y, w, h, ch(self, 'bar'))
        for (x0, x1, i), (name, _) in zip(self.bar_items(), self.menus()):
            s.text(x0 + 4, y + 2, name, ch(self, 'bar_text'))
        t = self.d.TITLE
        s.text(w - 6, y + 2, t, ch(self, 'dim'), align='right')

    def draw_play(self, s):
        e = self.e
        p = self.play
        v = self.view
        viewer = self.viewer()
        self.draw_bar(s)
        v.draw_base(s)
        # highlights
        if p.reach and p.human():
            # what the selected unit can't reach goes dark
            x, y, w, h = v.rect
            s.darken(x, y, w, h, 0.7)
            u = p.selected_unit()
            shown = set(v.visible_hexes())
            for hx in list(p.reach) + ([u.hex] if u else []):
                if hx in shown:
                    v.restore(s, hx)
            # a map too dark for darkening to show (space) tints what can
            # be reached instead: REACH = colour
            lit = getattr(self.d, 'REACH', None)
            if lit:
                for hx in p.reach:
                    if hx in shown:
                        v.tint(s, hx, lit, 0.3)
            if u:
                for hx in p.reach:
                    if hx in shown and hx in e.enemy_hexes(u.side):
                        v.outline(s, hx, rgb('#ff3010'), 2)
        if p.human() and e.phase == 'combat' and not p.pending:
            for h in e.targets():
                if h != p.target:
                    v.tint(s, h, '#ff2000', 0.25)
        if p.target is not None:
            v.tint(s, p.target, '#ff2000', 0.45)
            avail = e.attackers_for(p.target) + e.supporters_for(p.target)
            for u in avail:
                v.outline(s, u.hex, rgb('#40ff40') if u.id in p.chosen
                          else rgb('#808080'), 2)
            v.outline(s, p.target, rgb('#ff3010'), 2)
        if p.pending:
            v.outline(s, p.pending['target'], rgb('#ffd040'), 2)
            for u in p.pending['advance']:
                if u.alive:
                    v.outline(s, u.hex, rgb('#40ff40') if u.id in p.chosen
                              else rgb('#a0a0a0'), 2)
        if p.cursor is not None and p.target is None and not p.sel:
            v.outline(s, p.cursor, rgb('#ffffff'), 1)
        # objectives
        for h, o in e.board.objectives.items():
            v.flag(s, h, e.control.get(h), o['vp'])
        hook = getattr(self.d, 'DRAW_MAP', None)
        if hook:                        # what a side knows of the map
            hook(self, s)
        # units
        moving = {a.uid for a in self.anims if isinstance(a, MoveAnim)}
        vis = e.visible(viewer)
        shown = set(v.visible_hexes())
        dims = set()
        if p.human():
            for u in e.alive(e.side):
                if (e.moving and u.mp <= 0 < u.max_mp) or \
                        (e.phase == 'combat' and (u.attacked or u.fired)):
                    dims.add(u.id)
        # ghosts: enemy units last seen here
        if viewer is not None:
            for uid, h in self.memory.get(viewer, {}).items():
                u = e.units[uid]
                if uid in vis or h not in shown or not u.alive:
                    continue
                if any(x.id in vis for x in e.at(h)):
                    continue
                v.draw_stack(s, h, [u], ghost=True)
        for h, us in e.where().items():
            if h not in shown:
                continue
            here = [u for u in p.stack_at(h) if u.id not in moving]
            if here:
                v.draw_stack(s, h, here, sel=set(p.sel), dims=dims)
        occupied = {h for h in shown if p.stack_at(h)}
        for h, text in e.board.labels:
            if h in shown:
                v.label(s, h, text, h in occupied)
        for a in self.anims:
            if isinstance(a, MoveAnim):
                u = e.units[a.uid]
                if u.alive or u.hex is None:
                    x, y = a.pos(v)
                    v.counter_at(s, u, x, y)
            else:
                a.draw(self, s)
        p.draw_strip(s)
        # frame and banner
        x, y, w, h = v.rect
        s.frame(x - 1, y - 1, w + 2, h + 2, ch(self, 'dark'))
        if self.banner:
            text = self.banner[0]
            lines = font.wrap(text, w - 40)
            bh = 6 + 11 * len(lines)
            bw = max(font.width(ln) for ln in lines) + 20
            bx, by = x + (w - bw) // 2, y + 8
            s.rect(bx, by, bw, bh, ch(self, 'panel'))
            s.bevel(bx, by, bw, bh, ch(self, 'light'), ch(self, 'dark'))
            for i, ln in enumerate(lines):
                s.text(x + w // 2, by + 4 + 11 * i, ln, ch(self, 'accent'),
                       align='center')
        # panels
        for wd, r in self.layout.items:
            wd.draw(self, s, r)

    # ---------------------------------------------------------- saving

    def has_save(self):
        return os.path.exists(self.save_path)

    def save(self, path=None):
        d = dict(version=1, engine=self.e.to_json(),
                 controllers=self.controllers,
                 memory={s: {uid: hid(h) for uid, h in m.items()}
                         for s, m in self.memory.items()},
                 ai={s: {uid: hid(h) for uid, h in ai.memory.items()}
                     for s, ai in self.ais.items()},
                 view=[self.view.zoom, self.view.cx, self.view.cy])
        try:
            tmp = (path or self.save_path) + '.tmp'
            with open(tmp, 'w') as fh:
                json.dump(d, fh)
            os.replace(tmp, path or self.save_path)
        except OSError:
            pass

    def load(self, path=None):
        try:
            with open(path or self.save_path) as fh:
                d = json.load(fh)
            e = Engine(self.d)
            e.from_json(d['engine'])
        except (OSError, ValueError, KeyError, TypeError):
            self.flash('No saved game could be read.')
            return False
        self.e = e
        self.controllers = d['controllers']
        self.memory = {s: {uid: parse(h) for uid, h in m.items()}
                       for s, m in d.get('memory', {}).items()}
        self.ais = {}
        for s, mem in d.get('ai', {}).items():
            ai = self.ai_for(s)
            ai.memory = {uid: parse(h) for uid, h in mem.items()}
        self.play = PlayMode(self)
        self.modes = [self.play]
        self.anims = []
        self.e.events = []
        z, cx, cy = d.get('view', [self.view.zoom, 0, 0])
        self.view.zoom = z
        self.relayout()
        self.view.cx, self.view.cy = cx, cy
        self.view.clamp()
        if e.over:
            self.flash(e.result, 4)
        self.dirty = True
        return True

    def load_settings(self):
        try:
            with open(self.settings_path) as fh:
                d = json.load(fh)
        except (OSError, ValueError):
            return
        self.view.zoom = d.get('zoom', self.view.zoom)
        self.style = d.get('style', self.style)
        self.smooth_text = d.get('smooth_text', True)
        self.view.grid = d.get('grid', True)
        self.speed = d.get('speed', self.speed)
        self.skill = d.get('skill', self.skill)
        if not d.get('sound', True):
            self.sound.on = False

    def save_settings(self):
        try:
            with open(self.settings_path, 'w') as fh:
                json.dump(dict(zoom=self.view.zoom, style=self.style,
                               smooth_text=self.smooth_text,
                               grid=self.view.grid, speed=self.speed,
                               skill=self.skill, sound=self.sound.on), fh)
        except OSError:
            pass


# ----------------------------------------------------------- building

class BuildMenu(Mode):
    """Building at a shipyard (a game with BUILDS): what can be built
    there, what each costs and what it is, and the treasury.  Tap one to
    build it (as many as there's money for); Done closes."""

    def __init__(self, hx):
        self.hx = hx
        self.rects = []

    def rows(self, g):
        e = g.e
        from .units import Unit
        out = []
        for kind, b in getattr(g.d, 'BUILDS', {}).items():
            probe = Unit(dict(b['unit'], side=e.side, id='?'), e.types)
            out.append((kind, b, probe, e.build_reason(kind, self.hx)))
        return out

    def box(self, g, n):
        W, H = g.layout.W, g.layout.H
        w = min(420, W - 16)
        h = min(H - 20, 24 + n * 24 + 26)
        return (W - w) // 2, (H - h) // 2, w, h

    def draw(self, g, s):
        e = g.e
        rows = self.rows(g)
        x, y, w, h = self.box(g, len(rows))
        s.rect(x + 4, y + 4, w, h, (0, 0, 0))
        s.rect(x, y, w, h, ch(g, 'panel'))
        s.bevel(x, y, w, h, ch(g, 'light'), ch(g, 'dark'), 2)
        s.rect(x + 2, y + 2, w - 4, 14, ch(g, 'bar'))
        s.text(x + w // 2, y + 4, fit('Build at %s' % e.place(self.hx),
                                      w - 120), ch(g, 'bar_text'),
               align='center')
        s.text(x + w - 8, y + 4, '%s %d' % (
            getattr(g.d, 'RESOURCE', 'Points'), e.treasury[e.side]),
            ch(g, 'accent'), align='right')
        self.rects = []
        yy = y + 22
        tw = w - 24 - 62
        for i, (kind, b, probe, why) in enumerate(rows):
            if yy + 22 > y + h - 24:
                break
            self.rects += draw_buttons(g, s, [('Build', kind, not why)],
                                       x + 10, yy + 2, 56, 15)
            s.text(x + 74, yy, fit('%d. %s  (%d)   %s' % (
                i + 1, b.get('name', kind), b.get('cost', 0),
                probe.values()), tw), ch(g, 'text') if not why
                else ch(g, 'dim'))
            note = b.get('about', '')
            if why and not why.startswith('costs'):
                note = why[:1].upper() + why[1:] + '.'
            s.text(x + 74, yy + 10, fit(note, tw),
                   ch(g, 'red') if why and not why.startswith('costs')
                   else ch(g, 'dim'))
            yy += 24
        self.rects += draw_buttons(g, s, [('Done', '_done')],
                                   x + (w - 90) // 2, y + h - 22, 90, 15)

    def build(self, g, kind):
        u = g.e.build(kind, self.hx)
        if u is None:
            g.sound.play('nope')
            return
        g.after_engine()
        g.play.select([u])

    def key(self, g, k):
        if k in ('esc', 'enter', 'space', 'd'):
            g.pop(self)
        elif k.isdigit():
            rows = self.rows(g)
            i = int(k) - 1
            if 0 <= i < len(rows):
                self.build(g, rows[i][0])

    def tap(self, g, x, y):
        v = hit(self.rects, x, y)
        if v == '_done':
            g.sound.play('click')
            g.pop(self)
        elif v is not None:
            self.build(g, v)
        g.dirty = True


# ---------------------------------------------------------------- charts

class Charts(Mode):
    """The combat results table and the terrain effects chart."""

    def __init__(self):
        self.rects = []

    def draw(self, g, s):
        e = g.e
        W, H = g.layout.W, g.layout.H
        w, h = min(620, W - 8), min(440, H - 20)
        x, y = (W - w) // 2, (H - h) // 2
        s.rect(x + 4, y + 4, w, h, (0, 0, 0))
        s.rect(x, y, w, h, ch(g, 'panel'))
        s.bevel(x, y, w, h, ch(g, 'light'), ch(g, 'dark'), 2)
        s.rect(x + 2, y + 2, w - 4, 14, ch(g, 'bar'))
        s.text(x + w // 2, y + 4, 'Combat results and terrain',
               ch(g, 'bar_text'), align='center')
        # the CRT
        cols = e.columns
        cw = min(48, (w - 40) // len(cols))
        tx = x + 10
        ty = y + 22
        s.text(tx, ty, 'Die', ch(g, 'dim'))
        for i, c in enumerate(cols):
            s.text(tx + 30 + i * cw + cw // 2, ty, c, ch(g, 'accent'),
                   align='center')
        for r, row in enumerate(e.table):
            yy = ty + 12 + r * 11
            s.text(tx + 6, yy, str(r + 1), ch(g, 'accent'))
            for i, res in enumerate(row):
                good = res['d'] or res['de'] or res['retreat']
                bad = res['a'] or res['ae']
                col = rgb('#80e080') if good and not bad else \
                    rgb('#ff8060') if bad and not good else ch(g, 'text')
                s.text(tx + 30 + i * cw + cw // 2, yy, res['text'], col,
                       align='center')
        yy = ty + 16 + len(e.table) * 11
        key = ' '.join(crt_key(e)) + '  Odds round down; terrain and ' \
            'other shifts move the column.'
        for ln in font.wrap(key, w - 20):
            s.text(tx, yy, ln, ch(g, 'dim'))
            yy += 10
        # terrain
        yy += 6
        from .terrain import swatch
        classes = sorted({mc for t in e.board.T.values()
                          for mc in t.get('move', {})})
        s.text(tx + 22, yy, 'Terrain', ch(g, 'accent'))
        for i, mc in enumerate(classes):
            s.text(tx + 150 + i * 48, yy, mc, ch(g, 'accent'))
        s.text(tx + 150 + len(classes) * 48, yy, 'Defence', ch(g, 'accent'))
        yy += 12
        used = sorted(set(e.board.hexes.values()),
                      key=lambda n: e.board.T[n].get('z', 0))
        for name in used:
            t = e.board.T[name]
            if yy > y + h - 40:
                break
            s.blit(swatch(t, 10), tx + 6, yy)
            s.text(tx + 22, yy, t['name'], ch(g, 'text'))
            for i, mc in enumerate(classes):
                c = t.get('move', {}).get(mc)
                s.text(tx + 150 + i * 48, yy, '-' if c is None or
                       t.get('impassable') else '%g' % c, ch(g, 'text'))
            sh = t.get('shift', 0)
            s.text(tx + 150 + len(classes) * 48, yy,
                   '%+d' % sh if sh else '-', ch(g, 'text'))
            yy += 11
        extra = []
        for k, sp in e.board.Rd.items():
            if any(v == k for v in e.board.roads.values()):
                extra.append('%s: %s' % (sp['name'], ', '.join(
                    '%s %g' % (m, c) for m, c in sp['cost'].items())))
        for k, sp in e.board.S.items():
            if any(v == k for v in e.board.rivers.values()):
                extra.append('%s: crossing +%s%s' % (
                    sp['name'], '/'.join('-' if c is None else '%g' % c
                                         for c in sp['cost'].values()),
                    ', attacks across at half' if sp.get('halve') else ''))
        for ln in extra:
            if yy > y + h - 30:
                break
            s.text(tx + 6, yy, fit(ln, w - 24), ch(g, 'dim'))
            yy += 10
        self.rects = draw_buttons(g, s, [('Close', 'close')],
                                  x + w // 2 - 40, y + h - 20, 80, 15)

    def key(self, g, k):
        if k in ('esc', 'enter', 'space', 't'):
            g.pop(self)

    def tap(self, g, x, y):
        g.pop(self)


def crt_key(e):
    """What the results on the combat table mean, for those it has."""
    rs = [r for row in e.table for r in row]
    out = []
    if any(r['a'] for r in rs):
        out.append('A1, A2: the attacker loses steps.')
    if any(r['d'] for r in rs):
        out.append('D1, D2: the defender does.')
    if any(r['retreat'] for r in rs):
        out.append('R: the defender retreats.')
    if any(r['text'] == 'EX' for r in rs):
        out.append('EX: both lose one.')
    if any(r.get('disable') for r in rs):
        out.append("D: disabled; it can't move or fire in its next turn, "
                   "and a second D destroys it.")
    if any(r['de'] for r in rs):
        out.append('%s: destroyed.' % '/'.join(sorted(
            {r['text'] for r in rs if r['de']})))
    if any(r['ae'] for r in rs):
        out.append('AE: the attackers are destroyed.')
    return out


HELP = [
    "Grognard games are played on a map of hexagons with counters for "
    "units, as on a table top. Each turn every side moves, then attacks. "
    "The panels show the date and weather, the score, the objectives and "
    "whose phase it is. The bar at the top has the menus.",

    "MOVING. Tap one of your units to select it: the hexes it can reach "
    "light up. Tap one to move there. Each unit has movement points; "
    "terrain costs more or less to enter, and roads are quickest. A unit "
    "that moves next to an enemy unit (into its zone of control) must "
    "stop, unless a friendly unit is already there. Selecting a stack "
    "shows all its units in a strip in the corner of the map: tap one to "
    "pick it, or Whole stack to move them together. Undo takes back a "
    "move until you meet the enemy. End move goes on to combat.",

    "FIGHTING. In the combat phase, enemy hexes you can attack are shaded "
    "red. Tap one: every unit that can join in is picked (outlined in "
    "green). Tap a hex of your units to leave them out or put them back. "
    "Artillery can join from a distance (its range is on the counter in "
    "brackets). The panel shows the odds, the shifts for terrain and "
    "the like, and what each roll of the die would do. Attack! rolls it.",

    "RESULTS are taken in steps: most units can lose one and fight on "
    "weaker (a light band across the top of the counter), and are "
    "destroyed when they lose their last. A defender forced back that "
    "can't retreat loses another step instead. If a hex is emptied, the "
    "attackers may advance into it. Each unit attacks once a turn, and "
    "each hex can be attacked once.",

    "SUPPLY. A unit that can't trace a line back to its side's supply "
    "(free of the enemy and their zones of control) is out of supply: a "
    "red corner on its counter. It moves at half speed and attacks at "
    "half strength. The enemy only shows when your units are near "
    "(fog of war): where you last saw them is marked with a ?.",

    "KEYS. Arrows scroll; + and - zoom; N next unit (or target); U undo; "
    "E or Space ends the phase; A or Enter attacks; Esc cancels or opens "
    "the menus; C finds the selected unit; T shows the combat and "
    "terrain charts; L the log; G the hex grid; P counter pictures; ? "
    "this help. Drag the map to scroll it, or use the arrows on the "
    "panel.",
]
