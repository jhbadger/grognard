"""The rules: the board, and the Engine that plays a game on it.

The Engine holds everything about a game in progress and knows nothing
about screens, so the computer player, the tests and the window all use
it the same way:

    reachable(unit)                 where a unit can move this phase
    move(unit, hex)                 move it there
    attackers_for(hex), supporters_for(hex)
    odds(hex, attackers, support)   the odds and column shifts
    resolve(hex, attackers, support)  fight it out
    advance(units, hex)             take ground after a fight
    end_phase()                     movement -> combat -> the other side

The sequence of play is the classic one.  Each game turn every side in
ORDER takes a player turn: reinforcements arrive and supply is traced,
then it moves (entering an enemy zone of control stops a unit, except
where friendly units already stand; stacking is limited),
then it attacks (adjacent units combine against one hex, artillery in
range adds its strength, as does the defender's within range of the
hex attacked, odds and terrain pick a column of the combat
results table, a die picks the row).  Losses are taken in steps;
defenders who must retreat and can't stand, and lose one more step
between them.
"""

import heapq
import random
import re

from . import hexgrid
from .hexgrid import parse, hid, neighbours, distance
from . import terrain as _terrain
from .units import Unit, UNIT_TYPES

LEGEND = {'.': 'clear', ',': 'clear', ':': 'fields', 'f': 'woods',
          'F': 'forest', 'h': 'hills', 'r': 'rough', 'm': 'marsh',
          't': 'town', 'C': 'city', '~': 'water', ' ': None}

# The default combat results table.  Columns are odds (attack:defence,
# rounded down in the defender's favour), rows the roll of one die.
#   A1, A2   the attackers lose 1 or 2 steps    D1, D2  the defenders do
#   DR       the defenders retreat a hex        D1R     both
#   EX       each side loses a step             DE, AE  eliminated
#   -        nothing happens
CRT = {
    'columns': ['1:2', '1:1', '1.5:1', '2:1', '3:1', '4:1', '5:1', '6:1'],
    'rows': [
        ['A2', 'A1', 'A1', 'A1', 'EX', 'DR', 'D1R', 'D1R'],
        ['A1', 'A1', 'A1', 'EX', 'DR', 'D1R', 'D1R', 'D2R'],
        ['A1', 'A1', '-', 'DR', 'D1R', 'D1R', 'D2R', 'D2R'],
        ['A1', '-', 'EX', 'D1R', 'D1R', 'D2R', 'D2R', 'DE'],
        ['-', 'EX', 'DR', 'D1R', 'D2R', 'D2R', 'DE', 'DE'],
        ['-', 'DR', 'D1R', 'D2R', 'D2R', 'DE', 'DE', 'DE'],
    ],
}

WEATHER = {
    'clear':    dict(name='Clear', icon='sun', air=True),
    'overcast': dict(name='Overcast', icon='cloud', air=False),
    'rain':     dict(name='Rain', icon='rain', air=False, move=1.5),
    'snow':     dict(name='Snow', icon='snow', air=False, move=1.5,
                     spot=1),
    'fog':      dict(name='Fog', icon='fog', air=False, spot=1),
    'mud':      dict(name='Mud', icon='rain', air=False, move=2),
}


def ratio(col):
    """'3:2' or '1.5:1' -> 1.5."""
    a, b = col.split(':')
    return float(a) / float(b)


def parse_result(s):
    """A combat result ('D1R', 'EX', 'AE'...) as a dict: a and d (steps
    lost), retreat (hexes), ae and de (eliminated)."""
    s = s.strip().upper()
    r = dict(text=s, a=0, d=0, retreat=0, ae=False, de=False)
    if s in ('-', 'NE', ''):
        return r
    if s == 'AE':
        r['ae'] = True
        return r
    if s == 'DE':
        r['de'] = True
        return r
    if s == 'EX':
        r['a'] = r['d'] = 1
        return r
    m = re.fullmatch(r'(?:A(\d+))?(?:(D)(\d+)?)?(?:(R)(\d+)?)?', s)
    if not m:
        raise ValueError('unknown combat result %r' % s)
    if m.group(1):
        r['a'] = int(m.group(1))
    if m.group(3):
        r['d'] = int(m.group(3))
    if m.group(4):
        r['retreat'] = int(m.group(5) or 1)
    return r


# ------------------------------------------------------------------ board

class Board:
    """The map: terrain, roads, rivers, names and objectives."""

    def __init__(self, gdef):
        self.T = _terrain.merge(_terrain.TERRAIN, getattr(gdef, 'TERRAIN',
                                                          None))
        self.S = _terrain.merge(_terrain.SIDES, getattr(gdef, 'HEXSIDES',
                                                        None), 'river')
        self.Rd = _terrain.merge(_terrain.ROADS, getattr(gdef, 'ROAD_TYPES',
                                                         None), 'road')
        legend = dict(LEGEND)
        legend.update(getattr(gdef, 'LEGEND', {}))
        rows = gdef.MAP
        if isinstance(rows, str):
            rows = [r for r in rows.strip('\n').split('\n')]
        self.rows = len(rows)
        self.cols = max(len(r) for r in rows)
        self.hexes = {}
        self.problems = []
        for r, row in enumerate(rows):
            for c, ch in enumerate(row.ljust(self.cols)):
                t = legend.get(ch, 'missing')
                if t == 'missing':
                    self.problems.append('map %s: no legend for %r'
                                         % (hid((c, r)), ch))
                    t = 'clear'
                if t is not None:
                    if t not in self.T:
                        self.problems.append('map: no terrain %r' % t)
                        t = 'clear'
                    self.hexes[(c, r)] = t
        self.roads = {}
        for kind, path in getattr(gdef, 'ROADS', []):
            # waypoints: the road runs straight from each to the next
            hs = [parse(path[0])]
            for h in path[1:]:
                hs += hexgrid.line(hs[-1], parse(h))[1:]
            for a, b in zip(hs, hs[1:]):
                self.roads[hexgrid.side(a, b)] = kind
        self.rivers = {}
        for kind, sides in getattr(gdef, 'RIVERS', []):
            pairs = []
            for s in sides:
                if isinstance(s, str) and ':' in s:     # '1418:S,SE'
                    h, ds = s.split(':')
                    for d in ds.split(','):
                        d = hexgrid.DIR_NAMES.index(d.strip().upper())
                        pairs.append((parse(h), hexgrid.neighbour(parse(h),
                                                                  d)))
                else:                                   # '1418/1419'
                    a, b = s.split('/') if isinstance(s, str) else s
                    pairs.append((parse(a), parse(b)))
            for a, b in pairs:
                if distance(a, b) != 1:
                    self.problems.append('%s %s/%s: not neighbours'
                                         % (kind, hid(a), hid(b)))
                    continue
                self.rivers[hexgrid.side(a, b)] = kind
        labels = getattr(gdef, 'LABELS', {})
        if isinstance(labels, dict):
            labels = list(labels.items())
        self.labels = [(parse(h), t) for h, t in labels]
        self.objectives = {}
        for h, spec in getattr(gdef, 'OBJECTIVES', {}).items():
            spec = dict(spec)
            spec.setdefault('vp', 1)
            spec.setdefault('name', dict(self.labels).get(parse(h), hid(
                parse(h))))
            self.objectives[parse(h)] = spec

    def on_map(self, h):
        return h in self.hexes

    def terrain(self, h):
        return self.T[self.hexes.get(h, 'water')] if h in self.hexes \
            else None

    def terrain_name(self, h):
        return self.hexes.get(h)

    def road(self, a, b):
        return self.roads.get(hexgrid.side(a, b))

    def river(self, a, b):
        k = self.rivers.get(hexgrid.side(a, b))
        return self.S[k] if k else None

    def has_road(self, h):
        return any(self.road(h, n) for n in neighbours(h))

    def edge(self, which):
        """The hexes along one edge of the map: 'N', 'S', 'E' or 'W'."""
        out = []
        for (c, r) in self.hexes:
            if (which == 'W' and c == 0) or \
                    (which == 'E' and c == self.cols - 1) or \
                    (which == 'N' and r == 0) or \
                    (which == 'S' and r == self.rows - 1):
                out.append((c, r))
        return sorted(out)

    def hex_list(self, spec):
        """Hexes from a spec: 'W' (an edge), '1210', or a list of either."""
        if spec is None:
            return []
        if isinstance(spec, str):
            spec = [spec]
        out = []
        for s in spec:
            if s in ('N', 'S', 'E', 'W'):
                out.extend(self.edge(s))
            else:
                out.append(parse(s))
        return out


# ----------------------------------------------------------------- engine

class Reach(dict):
    """Where a unit can go: {hex: (cost, parent)}, and .parent, the
    whole search tree (paths can pass through hexes it can't stop in)."""
    parent = None


class Engine:
    """A game in progress."""

    def __init__(self, gdef, seed=None):
        self.d = gdef
        self.board = Board(gdef)
        self.sides = {s['id']: dict(s) for s in gdef.SIDES}
        self.side_ids = [s['id'] for s in gdef.SIDES]
        self.order = list(getattr(gdef, 'ORDER', self.side_ids))
        self.types = dict(UNIT_TYPES)
        for k, v in getattr(gdef, 'UNIT_TYPES', {}).items():
            t = dict(self.types.get(k, self.types['infantry']))
            t.update(v)
            self.types[k] = t
        crt = getattr(gdef, 'CRT', CRT)
        self.columns = crt['columns']
        self.col_ratio = [ratio(c) for c in self.columns]
        self.table = [[parse_result(x) for x in row] for row in crt['rows']]
        self.die = len(self.table)
        self.weather_types = dict(WEATHER)
        self.weather_types.update(getattr(gdef, 'WEATHER_TYPES', {}))
        self.stack_limit = getattr(gdef, 'STACK', 3)
        self.turns = gdef.TURNS
        self.fog = getattr(gdef, 'FOG', True)
        self.rng = random.Random(seed)
        self.new()

    # ------------------------------------------------------------ setup

    def new(self):
        self.units = {}
        for spec in self.d.UNITS:
            u = Unit(spec, self.types)
            if u.id in self.units:
                raise ValueError('two units called %r' % u.id)
            self.units[u.id] = u
        self.turn = 1
        self.active = 0
        self.phase = 'move'
        self.control = {h: o.get('owner') for h, o in
                        self.board.objectives.items()}
        self.bonus = {s: 0 for s in self.side_ids}     # exits and the like
        self.lost = {s: 0 for s in self.side_ids}      # steps lost
        self.exited = {s: 0 for s in self.side_ids}    # steps off the map
        self.hit = set()            # hexes attacked this phase
        self.over = False
        self.winner = None
        self.result = ''
        self.messages = []
        self.events = []            # for the screen: ('move', id, path)...
        self.version = 0
        self._cache = {}
        self.begin_player_turn()

    def to_json(self):
        st = self.rng.getstate()
        return dict(
            turn=self.turn, active=self.active, phase=self.phase,
            control={hid(h): s for h, s in self.control.items()},
            bonus=self.bonus, lost=self.lost, exited=self.exited,
            hit=[hid(h) for h in self.hit], over=self.over,
            winner=self.winner, result=self.result,
            messages=self.messages[-60:],
            rng=[st[0], list(st[1]), st[2]],
            units={u.id: u.to_dict() for u in self.units.values()})

    def from_json(self, d):
        self.turn, self.active, self.phase = d['turn'], d['active'], \
            d['phase']
        self.control = {parse(h): s for h, s in d['control'].items()}
        self.bonus, self.lost = d['bonus'], d['lost']
        self.exited = d.get('exited', {s: 0 for s in self.side_ids})
        self.hit = {parse(h) for h in d.get('hit', [])}
        self.over, self.winner, self.result = d['over'], d['winner'], \
            d['result']
        self.messages = d.get('messages', [])
        r = d['rng']
        self.rng.setstate((r[0], tuple(r[1]), r[2]))
        for uid, ud in d['units'].items():
            if uid in self.units:
                self.units[uid].load(ud)
        self.changed()

    # ---------------------------------------------------------- helpers

    def changed(self):
        self.version += 1
        self._cache = {}

    def cached(self, key, fn):
        v = self._cache.get(key)
        if v is None:
            v = self._cache[key] = fn()
        return v

    def say(self, text):
        self.messages.append(text)
        self.events.append(('say', text))

    @property
    def side(self):
        return self.order[self.active]

    def side_name(self, s, key='name'):
        return self.sides[s].get(key) or self.sides[s]['name']

    def enemies(self, side):
        return [s for s in self.side_ids if s != side]

    def enemy(self, side):
        return self.enemies(side)[0]

    def alive(self, side=None):
        return [u for u in self.units.values() if u.alive and
                (side is None or u.side == side)]

    def where(self):
        """{hex: [units]} for every unit on the map."""
        def build():
            w = {}
            for u in self.units.values():
                if u.alive:
                    w.setdefault(u.hex, []).append(u)
            return w
        return self.cached('where', build)

    def at(self, h, side=None):
        return [u for u in self.where().get(h, [])
                if side is None or u.side == side]

    def owner_at(self, h):
        us = self.where().get(h)
        return us[0].side if us else None

    def weather(self, turn=None):
        turn = turn or self.turn
        w = getattr(self.d, 'WEATHER', None)
        name = 'clear'
        if isinstance(w, dict):
            for t in sorted(w):
                if t <= turn:
                    name = w[t]
        elif isinstance(w, (list, tuple)) and w:
            name = w[min(turn, len(w)) - 1]
        elif isinstance(w, str):
            name = w
        spec = dict(self.weather_types.get(name, self.weather_types['clear']))
        spec['id'] = name
        return spec

    def has_air(self, side):
        return bool(self.weather().get('air')) and \
            side in getattr(self.d, 'AIR', ())

    def zoc(self, side):
        """Hexes in the zone of control of side's units."""
        def build():
            z = set()
            for u in self.alive(side):
                if u.zoc:
                    for n in neighbours(u.hex):
                        t = self.board.terrain(n)
                        if t and not t.get('impassable'):
                            riv = self.board.river(u.hex, n)
                            if riv and riv.get('cost', {}).get(
                                    u.move_class, 1) is None:
                                continue        # not across a major river
                            z.add(n)
            return z
        return self.cached(('zoc', side), build)

    def enemy_zoc(self, side):
        def build():
            z = set()
            for e in self.enemies(side):
                z |= self.zoc(e)
            return z
        return self.cached(('ezoc', side), build)

    def enemy_hexes(self, side):
        return self.cached(('ehex', side), lambda: {
            u.hex for u in self.units.values()
            if u.alive and u.side != side})

    def room(self, h, unit=None, side=None):
        """Whether unit can stop in h without breaking the stacking
        limit."""
        side = side or unit.side
        n = sum(u.stack for u in self.at(h, side) if u is not unit)
        return n + (unit.stack if unit else 1) <= self.stack_at(h)

    def stack_at(self, h):
        """The stacking limit in h: the game's STACK, unless the terrain
        sets its own (a city holds more)."""
        t = self.board.terrain(h)
        return t.get('stack', self.stack_limit) if t else self.stack_limit

    # --------------------------------------------------------- movement

    def enter_cost(self, unit, a, b, mclass=None):
        """Movement points for unit to go from a into neighbour b (None if
        it can't)."""
        mc = mclass or unit.move_class
        t = self.board.terrain(b)
        if t is None or t.get('impassable'):
            return None
        road = self.board.road(a, b)
        if road:
            c = self.board.Rd[road]['cost'].get(mc, 1)
            if c is not None:
                return c
        c = t['move'].get(mc, t['move'].get('foot'))
        if c is None:
            return None
        c = c * self.weather().get('move', 1)
        riv = self.board.river(a, b)
        if riv:
            rc = riv['cost'].get(mc, 1)
            if rc is None:
                return None
            c += rc
        return c

    def reachable(self, unit, mp=None):
        """{hex: (cost, parent hex)} for every hex the unit could end its
        move in this phase, from where it stands."""
        start = unit.hex
        mp = unit.mp if mp is None else mp
        if mp <= 0 or not unit.alive:
            return {}
        # friendly units cancel enemy zones of control where they stand
        friends = {u.hex for u in self.alive(unit.side) if u is not unit}
        ez = self.enemy_zoc(unit.side) - friends
        eh = self.enemy_hexes(unit.side)
        fresh = not unit.moved and mp >= unit.max_mp
        dist = {start: 0}
        parent = {start: None}
        heap = [(0, start)]
        while heap:
            cost, h = heapq.heappop(heap)
            if cost > dist[h]:
                continue
            if h != start and h in ez:
                continue                    # entering a ZOC ends the move
            for n in neighbours(h):
                if n in eh or not self.board.on_map(n):
                    continue
                if h in ez and n in ez:
                    continue                # no ZOC to ZOC
                c = self.enter_cost(unit, h, n)
                if c is None:
                    continue
                nc = cost + c
                if nc > mp + 1e-9:
                    # a fresh unit may always move one hex
                    if h == start and fresh:
                        nc = mp
                    else:
                        continue
                if nc < dist.get(n, 1e9):
                    dist[n] = nc
                    parent[n] = h
                    heapq.heappush(heap, (nc, n))
        out = Reach()
        out.parent = parent
        for h, c in dist.items():
            if h != start and self.room(h, unit):
                out[h] = (c, parent[h])
        return out

    def path(self, unit, dest, reach=None):
        if reach is None:
            reach = self.reachable(unit)
        parent = reach.parent
        if dest not in reach:
            return None
        p = [dest]
        while parent.get(p[-1]) is not None:
            p.append(parent[p[-1]])
        return p[::-1]

    def move(self, unit, dest):
        """Move unit to dest.  Returns its path, or None if it can't go."""
        reach = self.reachable(unit)
        if dest not in reach:
            return None
        path = self.path(unit, dest, reach)
        if unit.started is None:
            unit.started = unit.hex
        unit.hex = dest
        unit.mp = max(0, unit.mp - reach[dest][0])
        unit.moved = True
        self.changed()
        if dest in self.enemy_zoc(unit.side) and \
                len(self.at(dest, unit.side)) == 1:
            unit.mp = 0
        for h in path[1:]:
            self.take(h, unit.side)
        self.events.append(('move', unit.id, path))
        return path

    def take(self, h, side):
        if h in self.control and self.control[h] != side:
            self.control[h] = side
            o = self.board.objectives[h]
            self.say('%s take %s.' % (self.side_name(side), o['name']))
            self.events.append(('capture', h, side))

    # ----------------------------------------------------------- supply

    def supply_sources(self, side):
        cfg = getattr(self.d, 'SUPPLY', {}).get(side, {})
        return [h for h in self.board.hex_list(cfg.get('from', []))
                if h in self.board.hexes], cfg.get('range', 8)

    def supplied(self, side):
        """The hexes side can trace supply to."""
        def build():
            sources, rng = self.supply_sources(side)
            if not sources:
                return set(self.board.hexes)
            ez = self.enemy_zoc(side)
            eh = self.enemy_hexes(side)
            friends = {u.hex for u in self.alive(side)}
            ok = lambda h: h not in eh and (h not in ez or h in friends)
            dist = {}
            heap = []
            for s in sources:
                if ok(s):
                    dist[s] = 0
                    heap.append((0, s))
            heapq.heapify(heap)
            while heap:
                cost, h = heapq.heappop(heap)
                if cost > dist[h]:
                    continue
                for n in neighbours(h):
                    t = self.board.terrain(n)
                    if t is None or t.get('impassable') or not ok(n):
                        continue
                    road = self.board.road(h, n)
                    riv = self.board.river(h, n)
                    if riv and not road and \
                            riv['cost'].get('wheel', 1) is None:
                        continue
                    nc = cost + (0.5 if road else 1)
                    if nc <= rng and nc < dist.get(n, 1e9):
                        dist[n] = nc
                        heapq.heappush(heap, (nc, n))
            return set(dist)
        return self.cached(('supply', side), build)

    # ------------------------------------------------------- sequence

    def begin_player_turn(self):
        side = self.side
        self.phase = 'move'
        self.hit = set()
        self.arrivals(side)
        hook = getattr(self.d, 'ON_TURN', None)
        if hook:
            hook(self, side)
        sup = self.supplied(side)
        airdrop = self.weather().get('airdrop') == side or \
            side in self.weather().get('airdrop', ())
        for u in self.alive(side):
            u.oos = u.hex not in sup and not airdrop
            u.mp = u.max_mp / 2 if u.oos else u.max_mp
            u.moved = u.attacked = u.fired = False
            u.started = None
        for u in self.alive():
            u.dfired = False
            if u.side != side:
                u.seen = False
        oos = [u for u in self.alive(side) if u.oos]
        self.say('Turn %d: %s.' % (self.turn, self.side_name(side)))
        if oos:
            self.say('%d %s unit%s out of supply.' % (
                len(oos), self.side_name(side, 'adj'),
                's are' if len(oos) != 1 else ' is'))
        self.events.append(('turn', side))

    def arrivals(self, side):
        for u in self.units.values():
            if u.side != side or u.status != 'pending' or \
                    u.arrive > self.turn:
                continue
            spots = list(u.entry)
            for h in list(u.entry):
                spots += [n for n in neighbours(h) if n not in spots]
            eh = self.enemy_hexes(side)
            for h in spots:
                t = self.board.terrain(h)
                if t and not t.get('impassable') and h not in eh and \
                        self.room(h, u):
                    u.hex = h
                    u.status = 'map'
                    self.changed()
                    self.take(h, side)
                    self.say('%s arrives at %s.' % (u.long, self.place(h)))
                    self.events.append(('arrive', u.id))
                    break
            else:
                if u.entry:
                    self.say('%s is delayed.' % u.long)

    def exits(self, side):
        cfg = getattr(self.d, 'EXITS', {}).get(side)
        if not cfg:
            return
        hexes = set(self.board.hex_list(cfg.get('hexes')))
        for u in self.alive(side):
            if u.hex in hexes and not u.supports and u.attack_full > 0 and \
                    not u.type.get('no_exit'):
                vp = cfg.get('vp', 1) * u.steps
                self.bonus[side] += vp
                self.exited[side] += u.steps
                self.say('%s exits the map (%d VP).' % (u.long, vp))
                u.status = 'exited'
                u.hex = None
                self.changed()

    def end_phase(self):
        """The active side is done with this phase."""
        if self.over:
            return
        if self.phase == 'move':
            self.exits(self.side)
            self.phase = 'combat'
            self.hit = set()
            self.events.append(('phase', 'combat'))
            return
        self.active += 1
        if self.active >= len(self.order):
            self.active = 0
            self.end_turn()
            if self.over:
                return
        self.begin_player_turn()

    def end_turn(self):
        hook = getattr(self.d, 'ON_END_TURN', None)
        if hook:
            hook(self)
        for side, hexes in getattr(self.d, 'SUDDEN_DEATH', {}).items():
            hs = self.board.hex_list(hexes)
            if hs and all(self.control.get(h) == side for h in hs):
                names = ', '.join(self.place(h) for h in hs)
                self.finish(side, '%s hold %s. %s' % (
                    self.side_name(side), names,
                    'Sudden death victory.'))
                return
        if self.over:
            return
        if self.turn >= self.turns:
            self.finish()
            return
        self.turn += 1
        w0, w1 = self.weather(self.turn - 1), self.weather()
        if w0['id'] != w1['id']:
            self.say('The weather turns: %s.' % w1['name'].lower())

    # ----------------------------------------------------------- combat

    def can_attack(self, u):
        return u.alive and u.side == self.side and not u.attacked and \
            not u.supports and u.attack > 0

    def attackers_for(self, target):
        out = []
        for n in neighbours(target):
            for u in self.at(n, self.side):
                if self.can_attack(u):
                    riv = self.board.river(n, target)
                    if riv and riv['cost'].get(u.move_class, 1) is None and \
                            not riv.get('halve'):
                        continue
                    out.append(u)
        return out

    def supporters_for(self, target):
        return [u for u in self.alive(self.side)
                if u.supports and not u.fired and not u.attacked and
                distance(u.hex, target) <= u.range]

    def targets(self):
        """Enemy hexes the active side could attack now."""
        out = set()
        if self.phase != 'combat':
            return out
        for h in self.enemy_hexes(self.side):
            if h in self.hit:
                continue
            if self.attackers_for(h) or self.supporters_for(h):
                out.add(h)
        return out

    def column(self, att, dfn):
        r = att / max(1, dfn)
        col = -1
        for i, x in enumerate(self.col_ratio):
            if r + 1e-9 >= x:
                col = i
        return col

    def backing(self, target):
        """The defender's artillery that adds its strength to the
        defence of target: up to DEFENSIVE_FIRE (2) guns in range that
        haven't already fired in defence this turn, the strongest first."""
        n = getattr(self.d, 'DEFENSIVE_FIRE', 2)
        if not n:
            return []
        guns = [u for u in self.alive() if u.side != self.side and
                u.supports and not u.dfired and
                distance(u.hex, target) <= u.range]
        guns.sort(key=lambda u: (-u.attack, u.id))
        return guns[:n]

    def odds(self, target, attackers, support=()):
        """The odds of an attack: dict(att, dfn, col, shifts, final,
        label, bombard)."""
        defenders = [u for u in self.at(target) if u.side != self.side]
        att = 0.0
        notes = []
        for u in attackers:
            a = u.attack
            if u.oos:
                a /= 2
            riv = self.board.river(u.hex, target)
            if riv and riv.get('halve'):
                a /= 2
                if 'river' not in notes:
                    notes.append('river')
            att += a
        for u in support:
            att += u.attack / 2 if u.oos else u.attack
        att = int(att)
        dfn = sum(u.defense for u in defenders)
        backing = self.backing(target)
        dfn += sum(u.attack / 2 if u.oos else u.attack for u in backing)
        dfn = int(dfn)
        t = self.board.terrain(target)
        shifts = []
        if t.get('shift'):
            shifts.append((t['shift'], t['name']))
        o = self.board.objectives.get(target)
        if o and o.get('shift'):
            shifts.append((o['shift'], o.get('works', 'defences')))
        if attackers and t.get('open') and \
                any(u.is_armor for u in attackers) and \
                not any(u.is_at or u.is_armor for u in defenders):
            shifts.append((1, 'armour'))
        if self.has_air(self.side):
            shifts.append((1, 'air'))
        hook = getattr(self.d, 'COMBAT_SHIFTS', None)
        if hook:
            shifts += hook(self, target, attackers, support) or []
        col = self.column(att, dfn)
        final = col + sum(n for n, _ in shifts) if col >= 0 else -1
        if col >= 0:
            final = max(0, min(len(self.columns) - 1, final))
        return dict(att=att, dfn=max(1, dfn), col=col, shifts=shifts,
                    final=final, notes=notes, bombard=not attackers,
                    backing=[u.id for u in backing],
                    label=self.columns[final] if final >= 0 else
                    'too low')

    def outcomes(self, final):
        """The results a die could give on this column."""
        return [row[final] for row in self.table]

    def resolve(self, target, attackers, support=(), roll=None):
        """Fight it out.  Returns a dict: odds, roll, result, the steps
        each side lost, who retreated where, whether the hex is empty and
        who may advance into it."""
        attackers = list(attackers)
        support = list(support)
        o = self.odds(target, attackers, support)
        defenders = [u for u in self.at(target) if u.side != self.side]
        for u in attackers + defenders:
            u.seen = True
        for u in attackers:
            u.attacked = True
        for u in support:
            u.fired = True
        for uid in o.get('backing', []):
            self.units[uid].dfired = True
        self.hit.add(target)
        if o['final'] < 0 or not defenders:
            return dict(odds=o, roll=0, result=parse_result('-'),
                        alost=0, dlost=0, retreats=[], vacated=False,
                        advance=[], target=target)
        if roll is None:
            roll = self.rng.randint(1, self.die)
        res = dict(self.table[roll - 1][o['final']])
        if o['bombard']:                    # artillery alone can't lose
            res['a'] = 0
            res['ae'] = False
        out = dict(odds=o, roll=roll, result=res, target=target,
                   retreats=[], alost=0, dlost=0)
        dl = sum(u.steps for u in defenders) if res['de'] else res['d']
        out['dlost'] = self.take_losses(defenders, dl)
        if attackers:
            al = sum(u.steps for u in attackers) if res['ae'] else res['a']
            out['alost'] = self.take_losses(attackers, al)
        t = self.board.terrain(target)
        obj = self.board.objectives.get(target, {})
        if res['retreat'] and (t.get('stand') or obj.get('stand')):
            # a city (or a fortress) is held, not given up: a step instead
            out['dlost'] += self.take_losses(defenders, 1)
            out['stood'] = True
            res['retreat'] = 0
        if res['retreat']:
            # each retreats if it can; those that can't stand, and the
            # hex loses one more step between them
            from_hexes = [u.hex for u in attackers + support if u.alive]
            stuck = []
            for u in [u for u in defenders if u.alive]:
                path = self.retreat(u, res['retreat'], from_hexes)
                out['retreats'].append((u.id, path))
                if path is None:
                    stuck.append(u)
            if stuck:
                out['dlost'] += self.take_losses(stuck, 1)
                self.say('Cut off, they stand and fight.')
        self.changed()
        out['vacated'] = not self.at(target)
        out['advance'] = [u for u in attackers if u.alive] \
            if out['vacated'] else []
        self.say('%s at %s: %s, rolled %d: %s.' % (
            'Barrage' if o['bombard'] else 'Attack', self.place(target),
            o['label'], roll, res['text']))
        if out['dlost'] or out['alost']:
            self.say('%s lose %d step%s, %s %d.' % (
                self.side_name(self.enemy(self.side)), out['dlost'],
                '' if out['dlost'] == 1 else 's',
                self.side_name(self.side), out['alost']))
        self.events.append(('combat', target, out))
        return out

    def take_losses(self, units, n):
        """Take n steps from units, the strongest first.  Returns the
        steps taken."""
        taken = 0
        for _ in range(n):
            live = [u for u in units if u.alive]
            if not live:
                break
            u = max(live, key=lambda u: (u.steps, u.attack + u.defense))
            u.steps -= 1
            taken += 1
            self.lost[u.side] += 1
            if u.steps <= 0:
                self.eliminate(u)
        if taken:
            self.changed()
        return taken

    def eliminate(self, u):
        u.status = 'dead'
        self.events.append(('die', u.id, u.hex))
        self.say('%s is destroyed.' % u.long)
        u.hex = None
        self.changed()

    def retreat(self, u, n, from_hexes):
        """Retreat u n hexes away from from_hexes.  Returns its path, or
        None if it couldn't (and stays put)."""
        path = [u.hex]
        for _ in range(n):
            h = self.retreat_hex(u, path[-1], from_hexes, path)
            if h is None:
                return None
            path.append(h)
        u.hex = path[-1]
        self.changed()
        self.events.append(('retreat', u.id, path))
        return path

    def retreat_hex(self, u, frm, from_hexes, avoid=()):
        ez = self.enemy_zoc(u.side)
        eh = self.enemy_hexes(u.side)
        best = None
        for n in neighbours(frm):
            if n in avoid or n in eh or self.enter_cost(u, frm, n) is None:
                continue
            friends = self.at(n, u.side)
            if n in ez and not friends:
                continue
            if not self.room(n, u):
                continue
            away = min([distance(n, f) for f in from_hexes] or [3])
            t = self.board.terrain(n)
            score = away * 10 - (t.get('shift', 0) * 3) + \
                (2 if n in self.supplied(u.side) else 0) + \
                self.rng.random()
            if best is None or score > best[0]:
                best = (score, n)
        return best[1] if best else None

    def advance(self, units, target):
        """Units that won a fight move into the hex they took."""
        moved = []
        for u in units:
            if u.alive and self.room(target, u) and \
                    distance(u.hex, target) == 1 and \
                    not self.at(target, self.enemy(u.side)):
                path = [u.hex, target]
                u.hex = target
                self.changed()
                moved.append(u)
                self.events.append(('move', u.id, path))
        if moved:
            self.take(target, moved[0].side)
        return moved

    # -------------------------------------------------------- the score

    def vp(self, side):
        """Victory points: objectives held, the enemy's lost steps (at
        STEP_VP each, if the game gives any), and the bonus (exits)."""
        n = sum(o['vp'] for h, o in self.board.objectives.items()
                if self.control.get(h) == side and
                o.get('for', side) == side)
        per = getattr(self.d, 'STEP_VP', {})
        per = per.get(side, 0) if isinstance(per, dict) else per
        for e in self.enemies(side):
            n += self.lost[e] * per
        return n + self.bonus[side]

    def finish(self, winner=None, text=None):
        """The game is over."""
        self.over = True
        if text is None:
            fn = getattr(self.d, 'VICTORY', None)
            if fn:
                winner, text = fn(self)
            else:
                a, b = self.side_ids[:2]
                va, vb = self.vp(a), self.vp(b)
                margin = getattr(self.d, 'DECISIVE', 10)
                if va == vb:
                    winner, text = None, 'A draw, %d to %d.' % (va, vb)
                else:
                    winner = a if va > vb else b
                    m = abs(va - vb)
                    text = '%s %s victory, %d VP to %d.' % (
                        self.side_name(winner, 'adj'),
                        'decisive' if m >= margin else 'marginal',
                        max(va, vb), min(va, vb))
        self.winner, self.result = winner, text
        self.say(text)
        self.events.append(('over', winner))

    # ------------------------------------------------------ what's seen

    def visible(self, viewer):
        """Ids of the units viewer's side can see (fog of war)."""
        def build():
            if not self.fog or viewer is None:
                return {u.id for u in self.alive()}
            mine = self.alive(viewer)
            wspot = self.weather().get('spot')
            out = {u.id for u in mine}
            for u in self.alive():
                if u.side == viewer:
                    continue
                if u.seen:
                    out.add(u.id)
                    continue
                t = self.board.terrain(u.hex)
                for v in mine:
                    d = distance(u.hex, v.hex)
                    spot = v.spot if wspot is None else min(v.spot, wspot)
                    if d <= 1 or (d <= spot and t.get('los', True)):
                        out.add(u.id)
                        break
            return out
        return self.cached(('vis', viewer), build)

    # ----------------------------------------------------------- words

    def place(self, h):
        """A hex's name: the objective or label there, or its number."""
        o = self.board.objectives.get(h)
        if o:
            return o['name']
        for lh, t in self.board.labels:
            if lh == h:
                return t
        return hid(h)

    def date(self, turn=None):
        """('19 Dec 1944', 'AM') for a turn, from START and TURN_PARTS."""
        turn = turn or self.turn
        fn = getattr(self.d, 'TURN_NAME', None)
        if fn:
            return fn(turn)
        start = getattr(self.d, 'START', None)
        parts = getattr(self.d, 'TURN_PARTS', [''])
        if not start:
            return ('Turn %d' % turn, '')
        import datetime
        day = datetime.date(*start) + datetime.timedelta(
            days=(turn - 1) // len(parts))
        return (day.strftime('%d %b %Y').lstrip('0'),
                parts[(turn - 1) % len(parts)])
