"""Units: the counters.

A game lists its units in UNITS, each a dict:

    id        a short unique name ('501', '3/Pz3'); the default for name
    name      what the counter says ('501'), and long, the full name
              ('501st Parachute Infantry Regiment')
    side      which side it's on (one of the game's SIDES)
    type      a key of UNIT_TYPES (infantry, armor, artillery...)
    size      'XX', 'X', 'III', 'II' or 'I' (drawn over the symbol)
    a, d, m   attack, defence and movement allowance
    range     for artillery: how far away it can support an attack (and
              with RANGED = True, how far any unit can fire)
    m2        movement in the second movement phase (PHASES with 'move2')
    vp        what destroying it is worth to the enemy
    release   the turn it may first move and attack (held until then)
    fate      what the log says when it's lost ('is destroyed'; a ship
              'strikes her colours'); a type can say it too
    overrun   False if it can't overrun (with OVERRUN = True)
    steps     how many losses it can take (2 is usual: full, then reduced)
    ra, rd    attack and defence with one step left (default: halved)
    hex       where it starts ('1210'), or
    arrive    the turn it arrives on and at, where (a hex or a list)
    formation the division (or whatever) it belongs to, for the info panel

UNIT_TYPES says what each type of unit is: its NATO symbol (or picture),
movement class, whether it has a zone of control, whether it is armour
(for the armour bonus) or anti-tank (which cancels it), and whether it
supports attacks from a distance (artillery), and how much of a hex's
stacking limit it takes ('stack', 1 unless it's an HQ).  A game adds or changes
types with UNIT_TYPES in its script.
"""

import math

UNIT_TYPES = {
    'infantry':  dict(name='Infantry', symbol='infantry', move='foot'),
    'para':      dict(name='Airborne infantry', symbol='para', move='foot'),
    'glider':    dict(name='Glider infantry', symbol='glider', move='foot'),
    'mountain':  dict(name='Mountain infantry', symbol='mountain',
                      move='foot'),
    'motorized': dict(name='Motorized infantry', symbol='motorized',
                      move='wheel'),
    'mech':      dict(name='Panzergrenadiers', symbol='mech', move='track',
                      armor=False),
    'armor':     dict(name='Armour', symbol='armor', move='track',
                      armor=True),
    'td':        dict(name='Tank destroyers', symbol='td', move='track',
                      at=True),
    'antitank':  dict(name='Anti-tank', symbol='antitank', move='wheel',
                      at=True),
    'recon':     dict(name='Reconnaissance', symbol='recon', move='wheel',
                      spot=3),
    'cavalry':   dict(name='Cavalry', symbol='recon', move='track', spot=3,
                      armor=True),
    'engineer':  dict(name='Engineers', symbol='engineer', move='foot'),
    'artillery': dict(name='Artillery', symbol='artillery', move='wheel',
                      zoc=False, support=True),
    'sp_art':    dict(name='Self-propelled artillery', symbol='sp_art',
                      move='track', zoc=False, support=True),
    'rocket':    dict(name='Rocket artillery', symbol='rocket', move='wheel',
                      zoc=False, support=True),
    'hq':        dict(name='Headquarters', symbol='hq', move='wheel',
                      zoc=False, stack=0),
}

SIZES = {'XXX': 'corps', 'XX': 'division', 'X': 'brigade',
         'III': 'regiment', 'II': 'battalion', 'I': 'company',
         '***': 'platoon'}


class Unit:
    """One counter, and what it has done this turn."""

    SAVED = ('id', 'steps', 'hex', 'status', 'mp', 'moved', 'attacked',
             'fired', 'dfired', 'disabled', 'recovering', 'oos', 'seen',
             'arrive', 'started')

    def __init__(self, spec, types):
        self.spec = spec
        self.id = spec['id']
        self.side = spec['side']
        self.kind = spec.get('type', 'infantry')
        self.type = types.get(self.kind) or types['infantry']
        self.name = spec.get('name', self.id)
        self.long = spec.get('long', self.name)
        self.size = spec.get('size', '')
        self.formation = spec.get('formation', '')
        self.max_steps = spec.get('steps', 2)
        self.steps = self.max_steps
        self.range = spec.get('range', 0)
        self.max_mp = spec.get('m', 4)
        from .hexgrid import parse
        if spec.get('hex'):
            self.hex = parse(spec['hex'])
            self.status = 'map'
            self.arrive = 0
        else:
            self.hex = None
            self.status = 'pending'
            self.arrive = spec.get('arrive', 1)
        at = spec.get('at') or []
        if isinstance(at, str):
            at = [at]
        self.entry = [parse(h) for h in at]
        self.mp = self.max_mp
        self.moved = False          # moved at all this phase
        self.started = None         # where it began the phase (for undo)
        self.attacked = False       # made or joined an attack this turn
        self.fired = False          # artillery: supported this turn
        self.dfired = False         # artillery: fired in defence
        self.disabled = False       # a 'D' result: out of action a turn
        self.recovering = False     # sitting out its turn, disabled
        self.oos = False            # out of supply
        self.seen = False           # the enemy has seen it (fog of war)

    # ------------------------------------------------------- what it is

    @property
    def alive(self):
        return self.status == 'map'

    @property
    def move_class(self):
        return self.spec.get('move') or self.type.get('move', 'foot')

    @property
    def zoc(self):
        z = self.spec.get('zoc')
        if z is not None:
            return z
        return self.type.get('zoc', True) and self.attack_full > 0

    @property
    def is_armor(self):
        return bool(self.spec.get('armor', self.type.get('armor')))

    @property
    def is_at(self):
        return bool(self.spec.get('at', self.type.get('at')))

    @property
    def supports(self):
        """Artillery: adds its attack to fights within its range instead
        of attacking itself."""
        return bool(self.type.get('support')) and self.range > 0

    @property
    def stack(self):
        """How much of a hex's stacking limit it takes (HQs none)."""
        return self.spec.get('stack', self.type.get('stack', 1))

    @property
    def spot(self):
        return self.spec.get('spot', self.type.get('spot', 2))

    @property
    def m2(self):
        """Movement in a second movement phase."""
        return self.spec.get('m2', self.type.get('m2', 0))

    @property
    def reduced(self):
        return self.steps < self.max_steps

    def _value(self, full, reduced):
        if self.steps >= self.max_steps:
            return full
        if self.steps <= 1 and reduced is not None:
            return reduced
        if full <= 0:
            return 0
        return max(1, int(math.ceil(full * self.steps / self.max_steps)))

    @property
    def attack_full(self):
        return self.spec.get('a', 0)

    @property
    def attack(self):
        a = self._value(self.spec.get('a', 0), self.spec.get('ra'))
        return a

    @property
    def defense(self):
        return self._value(self.spec.get('d', 1), self.spec.get('rd'))

    def values(self):
        """What the counter's bottom line says: attack-defence-movement
        (with the range in brackets, for units that fire from afar)."""
        if self.supports or self.range > 1:
            return '%d(%d)-%d-%d' % (self.attack, self.range, self.defense,
                                     self.max_mp)
        return '%d-%d-%d' % (self.attack, self.defense, self.max_mp)

    def describe(self):
        return '%s %s' % (self.name, self.type.get('name', ''))

    # ---------------------------------------------------------- saving

    def to_dict(self):
        d = {k: getattr(self, k) for k in self.SAVED}
        d['hex'] = list(self.hex) if self.hex else None
        d['started'] = list(self.started) if self.started else None
        return d

    def load(self, d):
        for k in self.SAVED:
            if k in d:
                setattr(self, k, d[k])
        self.hex = tuple(d['hex']) if d.get('hex') else None
        self.started = tuple(d['started']) if d.get('started') else None
