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
    build(kind, hex)                spend the treasury on a new unit
    act(unit, key)                  a game's own order ('colonize')
    alter(hex, terrain)             change the map in play (a wood burnt)
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
# A game's own table may also use D alone (disabled: the defenders can't
# move or fire in their next turn; disabled again, they're destroyed) and
# X (destroyed: the same as DE).
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


# Phases a game can list in PHASES.  'move2' is a second movement phase
# after combat, for units with a second movement allowance ('m2').
MOVE_PHASES = ('move', 'move2')
PHASE_NAMES = {'move': 'Movement', 'combat': 'Combat',
               'move2': 'Second move'}


def ratio(col):
    """'3:2' or '1.5:1' -> 1.5."""
    a, b = col.split(':')
    return float(a) / float(b)


def parse_result(s):
    """A combat result ('D1R', 'EX', 'AE'...) as a dict: a and d (steps
    lost), retreat (hexes), ae and de (eliminated), disable."""
    s = s.strip().upper()
    r = dict(text=s, a=0, d=0, retreat=0, ae=False, de=False,
             disable=False)
    if s in ('-', 'NE', ''):
        return r
    if s == 'D':
        r['disable'] = True
        return r
    if s == 'X':
        r['de'] = True
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
        self.version = 0            # counts changes to the terrain
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
    overruns = frozenset()


class Engine:
    """A game in progress."""

    def __init__(self, gdef, seed=None):
        self.d = gdef
        self.board = Board(gdef)
        self.sides = {s['id']: dict(s) for s in gdef.SIDES}
        self.side_ids = [s['id'] for s in gdef.SIDES]
        # the sides that take turns; any other side (natives, say) never
        # moves, but can be attacked
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
        # optional rules
        self.phases = list(getattr(gdef, 'PHASES', ['move', 'combat']))
        self.ranged = getattr(gdef, 'RANGED', False)
        self.use_zoc = getattr(gdef, 'ZOC', True)
        self.overruns = getattr(gdef, 'OVERRUN', False)
        self.last_overrun = None
        self.rng = random.Random(seed)
        self.new()

    # ------------------------------------------------------------ setup

    def new(self):
        if getattr(self, 'altered', None):     # the map as it began
            self.board = Board(self.d)
        self.altered = {}           # hexes whose terrain changed in play
        self.units = {}
        self.spawned = []           # specs of the units made in the game
        self.serial = 0
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
        self.flags = {}             # a game's own state, kept in saves
        self.exited = {s: 0 for s in self.side_ids}    # steps off the map
        start = getattr(self.d, 'TREASURY', {})
        self.treasury = {s: start.get(s, 0) for s in self.side_ids}
        self.hit = set()            # hexes attacked this phase
        self.over = False
        self.winner = None
        self.result = ''
        self.messages = []
        self.events = []            # for the screen: ('move', id, path)...
        self.version = 0
        self._cache = {}
        hook = getattr(self.d, 'SETUP', None)
        if hook:                    # a map dealt out afresh each game
            hook(self)
            self.events = []
        self.begin_player_turn()

    def to_json(self):
        st = self.rng.getstate()
        return dict(
            turn=self.turn, active=self.active, phase=self.phase,
            control={hid(h): s for h, s in self.control.items()},
            bonus=self.bonus, lost=self.lost, exited=self.exited,
            flags=self.flags, treasury=self.treasury,
            altered=self.altered,
            spawned=self.spawned, serial=self.serial,
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
        self.flags = d.get('flags', {})
        if self.altered:
            self.board = Board(self.d)
            self.altered = {}
        for h, name in d.get('altered', {}).items():
            self.alter(parse(h), name)
        self.treasury = d.get('treasury', self.treasury)
        # the units made in that game, not the ones SETUP made in this one
        for spec in self.spawned:
            self.units.pop(spec['id'], None)
        self.spawned = []
        for spec in d.get('spawned', []):
            self.spawn(spec)
        self.serial = d.get('serial', 0)
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

    def say(self, text, side=None):
        """Add text to the log; with side, only that side reads it (what
        it built, where it settled)."""
        self.messages.append(text if side is None else [side, text])
        self.events.append(('say', text))

    def log(self, viewer=None, n=None):
        """The log as viewer may read it (None: all of it), the last n
        lines."""
        out = [m if isinstance(m, str) else m[1] for m in self.messages
               if isinstance(m, str) or viewer is None or m[0] == viewer]
        return out[-n:] if n else out

    # ------------------------------------------------- units made in play

    def spawn(self, spec):
        """A new unit, made during the game (built, founded, dealt out by
        SETUP): spec as in UNITS, with an id made up if it has none.  It's
        kept in saves."""
        spec = dict(spec)
        if not spec.get('id'):
            self.serial += 1
            spec['id'] = '%s%d' % (spec.get('type', 'u')[:3], self.serial)
            while spec['id'] in self.units:
                self.serial += 1
                spec['id'] = '%s%d' % (spec.get('type', 'u')[:3],
                                       self.serial)
        if spec['id'] in self.units:
            raise ValueError('two units called %r' % spec['id'])
        u = Unit(spec, self.types)
        self.units[u.id] = u
        self.spawned.append(spec)
        self.changed()
        return u

    def alter(self, h, name):
        """Change the terrain of hex h to name (a wood burnt to stumps,
        a bridge blown): kept in saves, and the map is painted again."""
        if name not in self.board.T:
            raise ValueError('no terrain %r' % name)
        self.board.hexes[h] = name
        self.board.version += 1
        self.altered[hid(h)] = name
        self.changed()

    def remove(self, u):
        """Take a unit off the map without a fight (a colony ship that
        has settled): not lost, not scored."""
        u.status = 'gone'
        u.hex = None
        self.changed()

    # ------------------------------------------------------- production

    def income(self, side):
        """What side earns at the start of its turn: INCOME(engine,
        side), if the game has production."""
        fn = getattr(self.d, 'INCOME', None)
        return fn(self, side) if fn else 0

    def build_sites(self, side):
        """Hexes where side may build: BUILD_SITES(engine, side), or
        wherever it has a unit whose type says 'factory'."""
        fn = getattr(self.d, 'BUILD_SITES', None)
        if fn:
            return list(fn(self, side))
        return sorted({u.hex for u in self.alive(side)
                       if u.type.get('factory')})

    def build_reason(self, kind, h):
        """Why the active side can't build kind at h now, or None if it
        can."""
        b = getattr(self.d, 'BUILDS', {}).get(kind)
        side = self.side
        if b is None:
            return 'nothing called %s' % kind
        if self.over or self.phase != self.phases[0] or not self.moving:
            return 'only in the movement phase'
        if h not in self.build_sites(side):
            return 'no shipyard here'
        if b.get('cost', 0) > self.treasury[side]:
            return 'costs %d' % b.get('cost', 0)
        fn = getattr(self.d, 'CAN_BUILD', None)
        if fn:
            why = fn(self, side, kind, h)
            if why:
                return why
        spec = dict(b['unit'], side=side)
        probe = Unit(dict(spec, id='?'), self.types)
        if not self.room(h, probe):
            return 'no room'
        return None

    def build(self, kind, h):
        """Build kind at h for the active side, paying for it from its
        treasury.  Returns the new unit (None if it can't): it may move
        at once."""
        if self.build_reason(kind, h):
            return None
        b = self.d.BUILDS[kind]
        side = self.side
        self.treasury[side] -= b.get('cost', 0)
        spec = dict(b['unit'], side=side, hex=hid(h))
        spec.setdefault('type', kind)
        spec.pop('id', None)
        self.serial += 1
        spec['id'] = '%s-%s%d' % (side, kind, self.serial)
        u = self.spawn(spec)
        self.say('%s built at %s.' % (b.get('name', kind), self.place(h)),
                 side)
        self.events.append(('build', u.id, h))
        hook = getattr(self.d, 'ON_BUILD', None)
        if hook:
            hook(self, u)
        return u

    # ----------------------------------------------------- unit orders

    def actions(self, u):
        """A game's own orders for u now: [(label, key, why not)], why
        not None for those it can give (ACTIONS(engine, unit))."""
        fn = getattr(self.d, 'ACTIONS', None)
        if not fn or self.over or not u.alive or u.side != self.side:
            return []
        return list(fn(self, u))

    def act(self, u, key):
        """Carry out one of u's actions (ACT(engine, unit, key)).  True if
        it was done."""
        for label, k, why in self.actions(u):
            if k == key and not why:
                self.d.ACT(self, u, key)
                self.changed()
                self.events.append(('act', u.id, key))
                return True
        return False

    @property
    def side(self):
        return self.order[self.active]

    @property
    def moving(self):
        """Whether this is a movement phase (the first or the second)."""
        return self.phase in MOVE_PHASES

    def phase_name(self, phase=None):
        names = dict(PHASE_NAMES)
        names.update(getattr(self.d, 'PHASE_NAMES', {}))
        return names.get(phase or self.phase, phase or self.phase)

    def held(self, u):
        """Whether u is on the map but may not yet move or attack: its
        'release' turn hasn't come."""
        return u.spec.get('release', 0) > self.turn

    def last_phase(self):
        return self.phase == self.phases[-1]

    def side_name(self, s, key='name'):
        return self.sides[s].get(key) or self.sides[s]['name']

    def verb(self, side, v):
        """v to go with the side's name: 'take' for the Germans, 'takes'
        for a side with a singular name ('singular': True, the Union)."""
        return v + 's' if self.sides[side].get('singular') else v

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
        """Hexes in the zone of control of side's units (none if the game
        plays without zones of control, ZOC = False)."""
        if not self.use_zoc:
            return set()

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
        hook = getattr(self.d, 'ENTER_COST', None)
        if hook:                        # the wind, or the like
            c = hook(self, unit, a, b, c)
        return c

    def reachable(self, unit, mp=None):
        """{hex: (cost, parent hex)} for every hex the unit could end its
        move in this phase, from where it stands."""
        start = unit.hex
        mp = unit.mp if mp is None else mp
        if mp <= 0 or not unit.alive:
            out = Reach()
            out.parent = {}
            return out
        # friendly units cancel enemy zones of control where they stand
        friends = {u.hex for u in self.alive(unit.side) if u is not unit}
        ez = self.enemy_zoc(unit.side) - friends
        eh = self.enemy_hexes(unit.side)
        fresh = not unit.moved and mp >= unit.max_mp
        may_overrun = self.can_overrun(unit)
        over = {}                   # enemy hexes it could overrun
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
                if not self.board.on_map(n):
                    continue
                if n in eh:
                    if may_overrun:
                        c = self.enter_cost(unit, h, n)
                        if c is not None and cost + c <= mp + 1e-9 and \
                                cost + c < over.get(n, (1e9,))[0]:
                            over[n] = (cost + c, h)
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
        out.parent = dict(parent)
        for h, c in dist.items():
            if h != start and self.room(h, unit):
                out[h] = (c, parent[h])
        out.overruns = set(over)
        for h, (c, p) in over.items():
            out[h] = (c, p)
            out.parent[h] = p
        return out

    def can_overrun(self, unit):
        """Whether unit may drive into an enemy hex in this movement phase
        and fight there (OVERRUN = True, in the first movement phase, for
        units that can attack and haven't, unless their type says
        'overrun': False)."""
        return self.overruns and self.phase == 'move' and \
            unit.attack > 0 and not unit.attacked and not unit.disabled and \
            unit.spec.get('overrun', unit.type.get('overrun', True))

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
        if dest in reach.overruns:
            return self.overrun(unit, path, reach)
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
        hook = getattr(self.d, 'ON_MOVE', None)
        if hook:                        # exploring, or the like
            hook(self, unit, path)
        return path

    def overrun(self, unit, path, reach):
        """unit drives up to the enemy in path's last hex and fights them
        there: the odds of its attack alone, terrain and all.  If the hex
        is cleared it moves in; either way its move is over.  The fight's
        result is in self.last_overrun."""
        target = path[-1]
        before = path[-2]
        unit.hex = before
        unit.mp = 0
        unit.moved = True
        self.changed()
        for h in path[1:-1]:
            self.take(h, unit.side)
        if len(path) > 2:
            self.events.append(('move', unit.id, path[:-1]))
        self.say('%s overruns %s.' % (unit.long, self.place(target)))
        res = self.resolve(target, [unit], [])
        res['overrun'] = True
        if res['vacated'] and unit.alive:
            unit.hex = target
            self.changed()
            self.take(target, unit.side)
            self.events.append(('move', unit.id, [before, target]))
        self.last_overrun = res
        return path

    def take(self, h, side):
        if h in self.control and self.control[h] != side:
            self.control[h] = side
            o = self.board.objectives[h]
            self.say('%s %s %s.' % (self.side_name(side),
                                    self.verb(side, 'take'), o['name']))
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
        self.phase = self.phases[0]
        self.hit = set()
        self.arrivals(side)
        self.treasury[side] += self.income(side)
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
            if u.disabled:              # sits this turn out
                u.mp = 0
                u.attacked = True
                u.recovering = True
            if self.held(u):            # waiting for the order to go
                u.mp = 0
                u.attacked = u.fired = True
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
        types = cfg.get('types')
        for u in self.alive(side):
            if types:
                ok = u.kind in types
            else:
                ok = not u.supports and u.attack_full > 0 and \
                    not u.type.get('no_exit')
            if u.hex in hexes and ok:
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
        if self.moving:
            self.exits(self.side)
        i = self.phases.index(self.phase)
        if i + 1 < len(self.phases):
            self.phase = self.phases[i + 1]
            self.start_phase()
            self.events.append(('phase', self.phase))
            return
        for u in self.alive(self.side):
            if u.recovering:            # back in action
                u.disabled = u.recovering = False
        self.active += 1
        if self.active >= len(self.order):
            self.active = 0
            self.end_turn()
            if self.over:
                return
        self.begin_player_turn()

    def start_phase(self):
        side = self.side
        if self.phase == 'combat':
            self.hit = set()
        elif self.phase == 'move2':
            for u in self.alive(side):
                m2 = u.spec.get('m2', u.type.get('m2', 0))
                u.mp = 0 if u.disabled else (m2 / 2 if u.oos else m2)
                u.moved = False
                u.started = None
            self.changed()

    def end_turn(self):
        hook = getattr(self.d, 'ON_END_TURN', None)
        if hook:
            hook(self)
            if self.over:           # the game's own ending came first
                return
        for side, hexes in getattr(self.d, 'SUDDEN_DEATH', {}).items():
            hs = self.board.hex_list(hexes)
            if hs and all(self.control.get(h) == side for h in hs):
                names = ', '.join(self.place(h) for h in hs)
                self.finish(side, '%s %s %s. %s' % (
                    self.side_name(side), self.verb(side, 'hold'), names,
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
            not u.supports and u.attack > 0 and not u.disabled

    def attackers_for(self, target):
        """The active side's units that could attack target: those next to
        it, or with RANGED = True, those within their range (at least
        one hex)."""
        if self.ranged:
            out = []
            for u in self.alive(self.side):
                if not self.can_attack(u):
                    continue
                d = distance(u.hex, target)
                if d > max(1, u.range):
                    continue
                if d == 1:
                    riv = self.board.river(u.hex, target)
                    if riv and riv['cost'].get(u.move_class, 1) is None \
                            and not riv.get('halve'):
                        continue
                out.append(u)
            return out
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

    def can_support(self, u):
        """Whether a gun may fire now: CAN_SUPPORT(engine, unit) can say
        no (out of ammunition)."""
        hook = getattr(self.d, 'CAN_SUPPORT', None)
        return hook is None or bool(hook(self, u))

    def supporters_for(self, target):
        return [u for u in self.alive(self.side)
                if u.supports and not u.fired and not u.attacked and
                distance(u.hex, target) <= u.range and self.can_support(u)]

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
        defence of target against an assault (not a bombardment): up to
        DEFENSIVE_FIRE (2) guns in range that haven't already fired in
        defence this turn, the strongest first."""
        n = getattr(self.d, 'DEFENSIVE_FIRE', 2)
        if not n:
            return []
        guns = [u for u in self.alive() if u.side != self.side and
                u.supports and not u.dfired and
                distance(u.hex, target) <= u.range and self.can_support(u)]
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
        # the defender's guns meet an assault (not a bombardment)
        backing = self.backing(target) if attackers else []
        dfn += sum(u.attack / 2 if u.oos else u.attack for u in backing)
        dfn = int(dfn)
        t = self.board.terrain(target)
        shifts = []
        if t.get('shift'):
            shifts.append((t['shift'], t['name']))
        # behind a wall: every adjacent attacker comes across one
        near = [u for u in attackers if distance(u.hex, target) == 1]
        walls = [self.board.river(u.hex, target) for u in near]
        if near and all(w and w.get('shift') for w in walls):
            w = max(walls, key=lambda w: w['shift'])
            shifts.append((w['shift'], w['name'].lower()))
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
                   retreats=[], alost=0, dlost=0,
                   sound=self.combat_sound(attackers, support))
        dl = sum(u.steps for u in defenders) if res['de'] else res['d']
        out['dlost'] = self.take_losses(defenders, dl)
        out['disabled'] = []
        if res.get('disable'):
            for u in [u for u in defenders if u.alive]:
                if u.disabled:          # twice is too much
                    out['dlost'] += self.take_losses([u], u.steps)
                else:
                    u.disabled = True
                    u.recovering = False
                    out['disabled'].append(u.id)
                    self.say('%s is disabled.' % u.long)
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
            loser = defenders[0].side
            self.say('%s %s %d step%s, %s %d.' % (
                self.side_name(loser), self.verb(loser, 'lose'),
                out['dlost'],
                '' if out['dlost'] == 1 else 's',
                self.side_name(self.side), out['alost']))
        self.events.append(('combat', target, out))
        return out

    def combat_sound(self, attackers, support):
        """The effect for a fight: the first unit's own (its 'fight'),
        or a barrage's boom, or the game's COMBAT_SOUND (gunfire)."""
        for u in list(attackers) + list(support):
            if u.fight:
                return u.fight
        if not attackers:
            return 'boom'
        return getattr(self.d, 'COMBAT_SOUND', 'gun')

    def take_losses(self, units, n):
        """Take n steps from units, the strongest first.  Returns the
        steps taken."""
        taken = 0
        for _ in range(n):
            live = [u for u in units if u.alive]
            if not live:
                break
            # the strongest first; what the others shield (a planet
            # under its fleet: 'under') last
            u = max(live, key=lambda u: (not u.type.get('under'), u.steps,
                                         u.attack + u.defense))
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
        if u.spec.get('vp'):            # what it's worth to the enemy
            for e in self.enemies(u.side):
                self.bonus[e] += u.spec['vp']
        self.events.append(('die', u.id, u.hex))
        self.say('%s %s.' % (u.long, u.spec.get(
            'fate', u.type.get('fate', 'is destroyed'))))
        where = u.hex
        u.hex = None
        self.changed()
        hook = getattr(self.d, 'ON_ELIMINATE', None)
        if hook:
            hook(self, u, where)

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
            # a game's own light: SPOT(engine, spotter, unit, spot) gives
            # how far spotter sees unit (the dark side of a moon, a
            # burning village)
            hook = getattr(self.d, 'SPOT', None)
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
                    if hook:
                        spot = hook(self, v, u, spot)
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
