"""The computer player.

It plays by the same rules and through the same Engine calls as a
person, one action at a time, so the screen can show each move:

    ai = AI(engine, 'de')
    ai.next_action()      ('move', unit id, hex), ('attack', hex,
                          [attacker ids], [artillery ids]) or ('end',)
    ai.choose_advance(result)   the units to send into a hex it took

It sees only what its side can see (fog of war), remembering where it
last saw each enemy unit.

Moving, it scores every hex each unit can reach: closeness to what it
wants (objectives to take or hold, the exit edge if the game has one),
the terrain, whether it can be supplied there, how much enemy strength
could reach it, and what it could attack from there.  A side's posture,
'attack' or 'defend' (the side's 'posture', or AI = {side: dict(...)}
in the game), sets how much each matters.

Fighting, it weighs every attack it could make against every hex in
reach by its expected result on the combat table, and makes the best
one; then it looks again, since the board has changed.

skill runs from 0 (careless) to 2 (careful): lower skill adds noise to
its judgement and makes it settle for worse odds.
"""

import heapq
import random

from .hexgrid import neighbours, distance, within


class AI:
    def __init__(self, engine, side, skill=1.0, seed=None):
        self.e = engine
        self.side = side
        self.skill = skill
        self.rng = random.Random(seed)
        spec = dict(engine.sides[side])
        spec.update(getattr(engine.d, 'AI', {}).get(side, {}))
        self.posture = spec.get('posture', 'attack')
        # enemy unit id -> last hex seen; it starts knowing where the
        # enemy began (the briefing)
        self.memory = {u.id: u.hex for u in engine.alive()
                       if u.side != side}
        self.key = None
        self.done = set()           # units already moved this phase
        self.fields = {}

    def posture_of(self, u):
        """'attack' or 'defend': the unit's own (a 'posture' in its spec,
        and from turn 'from' if it's a pair like ('attack', 9)), or its
        side's."""
        p = u.spec.get('posture')
        if isinstance(p, (tuple, list)):
            p = p[0] if self.e.turn >= p[1] else None
        return p or self.posture

    # ---------------------------------------------------------- seeing

    def look(self):
        e = self.e
        vis = e.visible(self.side) if e.fog else None
        for u in e.units.values():
            if u.side == self.side:
                continue
            if not u.alive:
                self.memory.pop(u.id, None)
            elif vis is None or u.id in vis:
                self.memory[u.id] = u.hex
        # a remembered unit that isn't where we can now see: forget it
        mine = [u.hex for u in e.alive(self.side)]
        for uid, h in list(self.memory.items()):
            u = e.units[uid]
            if vis is not None and uid not in vis and \
                    any(distance(h, m) <= 1 for m in mine):
                del self.memory[uid]

    def enemies(self):
        """[(unit, hex)] for the enemy units it knows of."""
        return [(self.e.units[uid], h) for uid, h in self.memory.items()]

    # -------------------------------------------------------- planning

    def begin(self):
        """Work out what this phase needs: the threat to each hex and how
        far each hex is from what this side wants."""
        e = self.e
        self.look()
        self.done = set()
        self.threat = {}
        for u, h in self.enemies():
            if u.supports:
                for x in within(h, u.range):
                    self.threat[x] = self.threat.get(x, 0) + u.attack * 0.7
                continue
            reach = int(u.max_mp / 1.6) + 1
            if e.ranged:
                reach += max(1, u.range) - 1
            for x in within(h, reach):
                self.threat[x] = self.threat.get(x, 0) + u.attack
        self.enemy_at = {}
        for u, h in self.enemies():
            self.enemy_at.setdefault(h, []).append(u)
        # what this side wants
        enemy = e.enemy(self.side)
        sd = getattr(e.d, 'SUDDEN_DEATH', {})
        self.must_hold = set(e.board.hex_list(sd.get(enemy)))
        self.must_take = set(e.board.hex_list(sd.get(self.side)))
        self.goals = []         # (hexes, value, kind)
        for h, o in e.board.objectives.items():
            mine = e.control.get(h) == self.side
            for_me = o.get('for', self.side) == self.side
            for_them = o.get('for', enemy) == enemy
            v = o['vp'] * (3 if h in self.must_hold or h in self.must_take
                           else 1)
            if mine and for_them:
                self.goals.append(([h], v, 'hold'))
            elif not mine and for_them and e.control.get(h):
                # the enemy took it and scores it: get it back
                self.goals.append(([h], v, 'retake'))
            elif not mine and (for_me or for_them):
                self.goals.append(([h], v, 'take'))
            elif not mine:
                self.goals.append(([h], v * 0.5, 'take'))
        # enemy units worth hunting down (a game marks them with a high
        # 'vp', 4 or more): where they were last seen
        for u, h in self.enemies():
            if u.spec.get('vp', 0) >= 4 and u.max_mp > 0:
                self.goals.append(([h], u.spec['vp'], 'hunt'))
        self.assign = {}
        if e.phase == 'move':
            self.garrisons()
        self.reserved = {h for uid, h in self.assign.items()
                         if e.units[uid].hex != h}
        ex = getattr(e.d, 'EXITS', {}).get(self.side)
        self.exit_types = None
        if ex:
            hs = [h for h in e.board.hex_list(ex.get('hexes'))]
            self.goals.append((hs, ex.get('vp', 1) * 2, 'exit'))
            self.exit_types = ex.get('types')
        self.fields = {}
        self.supplied = e.supplied(self.side)
        self.turns_left = e.turns - e.turn

    def garrisons(self):
        """Before moving, choose the best units in reach to hold each
        objective, the most valuable first: the strongest defenders, as
        many as the danger calls for."""
        e = self.e
        holds = sorted([(v, hs[0]) for hs, v, k in self.goals
                        if k == 'hold'], key=lambda x: (-x[0], x[1]))
        line = [u for u in e.alive(self.side)
                if not u.supports and u.attack_full > 0]
        reach = {u.id: e.reachable(u) for u in line}
        for value, h in holds:
            need = max(3 + value * 1.2, self.threat.get(h, 0) * 0.45)
            if value < 3 and self.threat.get(h, 0) == 0:
                continue
            have, room = 0, e.stack_at(h)
            # (stacking aside: whoever is in the way will move out)
            cands = [u for u in line if u.id not in self.assign and
                     (u.hex == h or h in reach[u.id].parent)]
            cands.sort(key=lambda u: (-u.defense, u.hex != h,
                                      distance(u.hex, h)))
            for u in cands:
                if have >= need or room < u.stack:
                    break
                self.assign[u.id] = h
                have += u.defense
                room -= u.stack

    def field(self, hexes, mclass):
        """Movement cost from every hex to the nearest of hexes, for a
        unit of mclass, ignoring other units."""
        key = (tuple(hexes), mclass)
        f = self.fields.get(key)
        if f is not None:
            return f
        e = self.e

        class Probe:
            move_class = mclass
        dist = {h: 0 for h in hexes if e.board.on_map(h)}
        heap = [(0, h) for h in dist]
        heapq.heapify(heap)
        while heap:
            c, h = heapq.heappop(heap)
            if c > dist[h]:
                continue
            for n in neighbours(h):
                if not e.board.on_map(n):
                    continue
                k = e.enter_cost(Probe, n, h)
                if k is None:
                    continue
                if c + k < dist.get(n, 1e9):
                    dist[n] = c + k
                    heapq.heappush(heap, (c + k, n))
        self.fields[key] = dist
        return dist

    # ------------------------------------------------------ the phases

    def next_action(self):
        e = self.e
        if e.over or e.side != self.side:
            return ('end',)
        key = (e.turn, e.side, e.phase)
        if key != self.key:
            self.key = key
            self.begin()
        if e.moving:
            return self.next_move()
        return self.next_attack()

    # ---------------------------------------------------------- moving

    def order(self):
        e = self.e
        units = [u for u in e.alive(self.side)
                 if u.id not in self.done and u.mp > 0]
        known = [h for _, h in self.enemies()]

        def near(u):
            return min([distance(u.hex, h) for h in known] or [99])
        holds = {hs[0] for hs, v, k in self.goals if k == 'hold'}

        def rank(u):
            rear = u.supports or u.attack_full == 0
            if u.hex in holds and u.stack and \
                    self.assign.get(u.id) != u.hex:
                return 0            # make room for a garrison first
            return 2 if rear else 1
        # then line units, nearest the enemy first; artillery and HQs last
        return sorted(units, key=lambda u: (rank(u), near(u), u.id))

    def next_move(self):
        for u in self.order():
            self.done.add(u.id)
            dest = self.best_hex(u)
            if dest is not None and dest != u.hex:
                return ('move', u.id, dest)
        return ('end',)

    def best_hex(self, u):
        e = self.e
        reach = e.reachable(u)
        cands = list(reach) + [u.hex]
        best, best_score = None, None
        noise = (2.0 - self.skill) * 1.5
        for h in cands:
            if h in reach.overruns:
                # drive in and fight: worth it for a good result
                v, o = self.expected(h, [u], [])
                if o['final'] < 0:
                    continue
                s = v * 5 - 2 + self.score(u, reach[h][1]) * 0.5
            else:
                s = self.score(u, h)
            s += self.rng.uniform(0, noise)
            if best_score is None or s > best_score:
                best, best_score = h, s
        return best

    def stack_defense(self, u, h):
        d = sum(x.defense for x in self.e.at(h, self.side) if x is not u)
        return d + u.defense

    def score(self, u, h):
        e = self.e
        attack = self.posture_of(u) == 'attack'
        t = e.board.terrain(h)
        s = 0.0
        # goals
        for hexes, value, kind in self.goals:
            f = self.field(hexes, u.move_class)
            d = f.get(h)
            if d is None:
                continue
            if kind == 'exit':
                if self.exit_types:
                    if u.kind not in self.exit_types:
                        continue
                elif u.supports or u.kind == 'hq' or not attack:
                    continue
                # worth more as the end approaches, and for strong units
                w = value * u.steps * (1.5 if self.turns_left < 6 else 1)
                if self.exit_types:
                    # units whose whole job is getting off the map: a
                    # steady pull, every hex nearer as good as the last
                    s += w * (3 - d * 0.25)
                else:
                    s += w * 2.0 / (1 + d / 2)
                if d == 0:
                    s += w * 3
            elif kind == 'take':
                if e.phase == 'move2' and attack:
                    continue        # after the fight: get clear first
                s += value * (3.0 if attack else 1.2) / (1 + d / 2)
            elif kind == 'retake':
                if e.phase == 'move2':
                    continue
                s += value * 3.0 / (1 + d / 2)
                if d <= 1 and u.attack > 0:
                    s += value * 0.8        # close enough to strike
            elif kind == 'hunt':
                if attack and u.attack > 0 and e.phase != 'move2':
                    s += value * 1.5 / (1 + max(0, d - u.range) / 2)
            else:       # hold
                h0 = hexes[0]
                if self.assign.get(u.id) == h0:
                    s += 60 if d == 0 else 30.0 / (1 + d)
                    continue
                if u.id in self.assign:
                    continue
                danger = self.threat.get(h0, 0)
                need = max(3 + value * 1.2, danger * 0.45)
                have = sum(x.defense for x in e.at(h0, self.side)
                           if x is not u and not x.supports)
                if u.supports or u.attack_full == 0:
                    short = 0       # guns and HQs don't make a garrison
                    if d == 0:
                        continue
                else:
                    short = max(0.0, need - have) / need
                if d == 0:
                    s += value * (3 if not attack else 1.5) * \
                        min(1.0, short + 0.2)
                else:
                    s += value * (1.0 if not attack else 0.3) * \
                        (0.3 + short) / (1 + d)
        # make way for a garrison on its way
        if h in self.reserved and self.assign.get(u.id) != h:
            s -= 30
        # terrain
        s -= t.get('shift', 0) * (2.5 if not attack else 1.2)
        # supply
        if h not in self.supplied:
            s -= 6
        # danger: enemy strength that could hit this hex, against the stack
        threat = self.threat.get(h, 0)
        if threat:
            dfn = self.stack_defense(u, h) * (1 + 0.5 * -t.get('shift', 0))
            ratio = threat * 0.5 / max(1, dfn)
            if ratio > 1.5:
                s -= (ratio - 1.5) * (4 if not attack else 2) * u.steps * \
                    (3 if e.phase == 'move2' else 1) * \
                    (u.spec.get('vp', u.steps) / u.steps)
        # contact
        adj_enemy = [x for n in neighbours(h) for x in self.enemy_at.get(n,
                                                                         [])]
        if u.supports:
            in_range = sum(1 for _, eh in self.enemies()
                           if distance(h, eh) <= u.range)
            s += min(in_range, 4) * 1.5
            for hexes, value, kind in self.goals:
                if kind == 'hold' and distance(h, hexes[0]) <= u.range:
                    s += min(value, 12) * (0.6 if not attack else 0.2)
            if adj_enemy:
                s -= 12
            if threat > 0:
                s -= threat * 0.05
        elif u.kind == 'hq':
            s -= threat * 0.3
            if adj_enemy:
                s -= 15
        elif e.ranged:
            # in range of something to shoot at (but not after the fight)
            r = max(1, u.range)
            near = [n for n in self.enemy_at if distance(h, n) <= r]
            if near and u.attack > 0 and e.phase != 'move2':
                weak = min(sum(x.defense for x in self.enemy_at[n])
                           for n in near)
                if attack:
                    s += 3 + max(0, u.attack - weak) * 0.6
                else:
                    s += 1
        else:
            if adj_enemy:
                weak = min(sum(x.defense for x in self.enemy_at[n])
                           for n in neighbours(h) if n in self.enemy_at)
                if attack:
                    s += 3 + max(0, u.attack - weak) * 0.6
                else:
                    s += 0.5
        # stay where you are, all else equal (saves the screen some motion)
        if h == u.hex:
            s += 0.3
        return s

    # -------------------------------------------------------- fighting

    def expected(self, target, attackers, support):
        """What an attack is worth, on average."""
        e = self.e
        o = e.odds(target, attackers, support)
        if o['final'] < 0:
            return -99, o
        defenders = [x for x in e.at(target) if x.side != self.side]
        dsteps = sum(x.steps for x in defenders)
        asteps = sum(x.steps for x in attackers)
        obj = e.board.objectives.get(target)
        objv = 0
        if obj:
            objv = obj['vp']
            if target in self.must_hold or target in self.must_take:
                objv *= 4
            enemy_scores = obj.get('for', e.enemy(self.side)) != self.side
            if enemy_scores and e.control.get(target) == self.side:
                objv *= 0.4
            elif enemy_scores and e.control.get(target) not in (
                    None, self.side):
                # the enemy is scoring it now: taking it back is worth
                # twice as much, and more as the end nears
                objv *= 2 * (1.5 if e.turns - e.turn < 3 else 1)
        worth = sum(x.spec.get('vp', x.steps) for x in defenders)
        dval = worth / max(1, dsteps) + \
            0.1 * sum(x.attack for x in defenders) / max(1, dsteps)
        bold = sum(1 for x in attackers + list(support)
                   if self.posture_of(x) == 'attack') * 2 >= \
            len(attackers) + len(support)
        aval = 1.0 if bold else 1.4
        total = 0.0
        for res in e.outcomes(o['final']):
            dl = dsteps if res['de'] else min(res['d'], dsteps)
            al = 0 if o['bombard'] else (asteps if res['ae'] else
                                         min(res['a'], asteps))
            v = dl * dval - al * aval
            if res.get('disable'):
                v += sum(x.steps if x.disabled else 0.45 * x.steps
                         for x in defenders) * dval
            if res['retreat'] and dl < dsteps:
                v += 0.6 + (objv * 0.8 if attackers else 0)
            elif dl >= dsteps and attackers:
                v += objv
            total += v
        return total / len(e.outcomes(o['final'])), o

    def next_attack(self):
        e = self.e
        caution = (1.0 - self.skill) * 0.3
        best = None
        for target in e.targets():
            att = sorted(e.attackers_for(target),
                         key=lambda x: -x.attack)
            sup = sorted(e.supporters_for(target),
                         key=lambda x: -x.attack)
            options = []
            for k in range(len(att) + 1):
                for j in range(len(sup) + 1):
                    if k == 0 and j == 0:
                        continue
                    options.append((att[:k], sup[:j]))
            for a, s in options:
                v, o = self.expected(target, a, s)
                if o['final'] < 0:
                    continue
                # keep units for other attacks: a little cost per unit
                cost = 0.12 * len(a) + 0.08 * len(s)
                if not a:
                    cost += 0.1         # artillery alone: keep some back
                bold = sum(1 for x in a + s
                           if self.posture_of(x) == 'attack') * 2 >= \
                    len(a) + len(s)
                score = v - cost + self.rng.uniform(
                    0, (2 - self.skill) * 0.15) - \
                    (0.15 if bold else 0.35) - caution
                if best is None or score > best[0]:
                    best = (score, target, a, s)
        if best and best[0] > 0:
            _, target, a, s = best
            return ('attack', target, [x.id for x in a], [x.id for x in s])
        return ('end',)

    def choose_advance(self, result):
        """Which of the units that may advance into a won hex should."""
        e = self.e
        # never walk out of a place that has to be held
        holds = {h for h, o in e.board.objectives.items()
                 if e.control.get(h) == self.side and
                 o.get('for', e.enemy(self.side)) != self.side}
        cands = [u for u in result.get('advance', [])
                 if u.alive and u.hex not in holds]
        if not cands:
            return []
        target = result['target']
        obj = e.board.objectives.get(target)
        t = e.board.terrain(target)
        want = 1
        if obj or t.get('shift', 0) < 0:
            want = e.stack_at(target)
        elif all(self.posture_of(u) != 'attack' for u in cands):
            want = 0
        cands.sort(key=lambda u: (-u.defense, u.id))
        return [u.id for u in cands[:want]]
