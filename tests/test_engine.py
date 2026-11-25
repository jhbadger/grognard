"""The engine's own tests: hex geometry, and the rules played out on a
tiny scenario."""

import unittest

import util
from grognard import hexgrid
from grognard.hexgrid import parse, hid, distance, neighbours
from grognard.rules import Engine, parse_result
from grognard.ai import AI


class Hexes(unittest.TestCase):
    def test_names(self):
        for h in [(0, 0), (11, 9), (25, 19)]:
            self.assertEqual(parse(hid(h)), h)
        self.assertEqual(hid((11, 9)), '1210')

    def test_neighbours(self):
        for h in [(3, 3), (4, 3), (0, 0)]:
            ns = neighbours(h)
            self.assertEqual(len(set(ns)), 6)
            for d, n in enumerate(ns):
                self.assertEqual(distance(h, n), 1)
                self.assertEqual(hexgrid.direction(h, n), d)
                self.assertIn(h, neighbours(n))

    def test_distance_and_line(self):
        a, b = (1, 2), (7, 5)
        self.assertEqual(distance(a, b), distance(b, a))
        ln = hexgrid.line(a, b)
        self.assertEqual(ln[0], a)
        self.assertEqual(ln[-1], b)
        self.assertEqual(len(ln), distance(a, b) + 1)
        for x, y in zip(ln, ln[1:]):
            self.assertEqual(distance(x, y), 1)
        self.assertEqual(len(hexgrid.ring((5, 5), 2)), 12)
        self.assertEqual(len(hexgrid.within((5, 5), 2)), 19)

    def test_stamp_tiles_the_plane(self):
        """Every pixel belongs to exactly one hex, and every hex is the
        stamp's shape."""
        from render_check import pixel_owners
        for zoom in ((16, 18), (24, 28), (36, 42)):
            g = hexgrid.Geometry(*zoom)
            counts = pixel_owners(g, 8 * g.dx, 7 * g.dy)
            inner = [n for (c, r), n in counts.items()
                     if 2 <= c <= 5 and 2 <= r <= 4]
            self.assertEqual(set(inner), {len(g.inside)})
            self.assertEqual(g.at(*g.center((3, 3))), (3, 3))


class SmoothText(unittest.TestCase):
    """Text recorded for the window to draw in a real font."""

    def setUp(self):
        from grognard import font
        font.set_metrics(lambda s, scale: len(s) * 5 * scale)
        self.addCleanup(font.set_metrics, None)

    def test_recorded_not_drawn(self):
        from grognard.gfx import Surface
        s = Surface(100, 50)
        s.texts = []
        w = s.text(50, 10, 'abc', (255, 255, 255), align='center')
        self.assertEqual(w, 15)
        self.assertEqual(s.texts, [(43, 10, 'abc', (255, 255, 255), None,
                                    1)])
        self.assertEqual(set(s.buf), {0})          # no pixels touched
        s.text(0, 30, '\x01', (255, 255, 255))     # the bitmap's arrow
        self.assertEqual(s.texts[-1][2], '\u2191')

    def test_covered_and_clipped(self):
        from grognard.gfx import Surface
        s = Surface(100, 50)
        s.texts = []
        s.text(5, 5, 'under', (255, 255, 255))
        s.text(5, 30, 'beside', (255, 255, 255))
        s.rect(0, 0, 40, 20, (0, 0, 0))             # a box over the first
        s.rect(0, 28, 1, 20, (0, 0, 0))             # a thin line: no matter
        self.assertEqual([t[2] for t in s.texts], ['beside'])
        s.set_clip(60, 0, 40, 50)
        s.text(0, 0, 'outside', (255, 255, 255))
        s.set_clip()
        self.assertEqual(len(s.texts), 1)
        s.fill((0, 0, 0))
        self.assertEqual(s.texts, [])


class Rules(unittest.TestCase):
    def setUp(self):
        self.e = Engine(util.tiny(), seed=1)

    def test_results(self):
        self.assertEqual(parse_result('D1R')['d'], 1)
        self.assertEqual(parse_result('D1R')['retreat'], 1)
        self.assertEqual(parse_result('DR')['retreat'], 1)
        self.assertEqual(parse_result('A2')['a'], 2)
        self.assertTrue(parse_result('DE')['de'])
        self.assertEqual(parse_result('EX')['a'], 1)
        with self.assertRaises(ValueError):
            parse_result('Q7')

    def test_roads_and_terrain(self):
        e = self.e
        b1 = e.units['b1']
        b1.hex = parse('0101')
        e.changed()
        r = e.reachable(b1)
        # a road costs half: 4 MP is 8 hexes along it, but the map's 8 wide
        self.assertIn(parse('0601'), r)
        self.assertEqual(r[parse('0301')][0], 1)
        # woods cost 2 to a foot unit
        b1.hex = parse('0203')
        e.changed()
        self.assertEqual(e.enter_cost(b1, parse('0203'), parse('0303')), 2)

    def test_river_and_water(self):
        e = self.e
        r1 = e.units['r1']
        self.assertEqual(e.enter_cost(r1, parse('0703'), parse('0603')),
                         1 + 2)
        self.assertIsNone(e.enter_cost(r1, parse('0204'), parse('0305')))

    def test_zoc_stops_movement(self):
        e = self.e
        b2 = e.units['b2']
        b2.hex = parse('0503')
        e.changed()
        r = e.reachable(b2)
        ez = e.enemy_zoc('b')
        for h in r:
            if h in ez:
                # nothing beyond a ZOC hex is reached through it
                for n in neighbours(h):
                    if n in r and r[n][1] == h:
                        self.fail('moved on from a ZOC hex %s' % hid(h))
        # ZOC to ZOC is not allowed
        b2.hex = parse('0603')
        e.changed()
        r = e.reachable(b2)
        self.assertTrue(parse('0603') in ez)
        for h in r:
            self.assertFalse(h in ez and r[h][1] == parse('0603'))

    def test_friends_cancel_zoc(self):
        e = self.e
        b1, b2 = e.units['b1'], e.units['b2']
        b1.hex = parse('0602')
        b2.hex = parse('0502')
        e.changed()
        self.assertIn(parse('0602'), e.enemy_zoc('b'))
        r = e.reachable(b2)
        self.assertIn(parse('0602'), r)

    def test_stacking(self):
        e = self.e
        b1, b2, ba = e.units['b1'], e.units['b2'], e.units['bA']
        b1.hex = b2.hex = parse('0202')
        e.changed()
        self.assertNotIn(parse('0202'), e.reachable(ba))

    def test_combat(self):
        e = self.e
        e.end_phase()                   # blue to combat
        b1, b2 = e.units['b1'], e.units['b2']
        r1 = e.units['r1']
        b1.hex, b2.hex = parse('0702'), parse('0603')
        e.changed()
        self.assertIn(r1.hex, e.targets())
        att = e.attackers_for(r1.hex)
        self.assertEqual({u.id for u in att}, {'b1', 'b2'})
        sup = e.supporters_for(r1.hex)
        self.assertEqual(sup, [])               # out of range
        o = e.odds(r1.hex, att, [])
        # 4 + half of 6 (across the river) = 7 against 4: 1.5:1, and one
        # column left for the hills (which also spoil the armour's bonus)
        self.assertEqual(o['att'], 7)
        self.assertEqual(e.columns[o['col']], '1.5:1')
        self.assertEqual(o['shifts'], [(-1, 'Hills')])
        self.assertEqual(o['label'], '1:1')
        res = e.resolve(r1.hex, att, [], roll=6)
        self.assertEqual(res['result']['text'], 'DR')
        self.assertEqual(r1.steps, 2)
        self.assertNotEqual(r1.hex, parse('0703'))
        self.assertTrue(res['vacated'])
        moved = e.advance([b1], parse('0703'))
        self.assertEqual(moved, [b1])
        self.assertTrue(b1.attacked and b2.attacked)
        self.assertNotIn(parse('0703'), e.targets())

    def test_cut_off_and_elimination(self):
        e = self.e
        e.end_phase()
        r2 = e.units['r2']
        b1, b2 = e.units['b1'], e.units['b2']
        # r2 at the map's edge, surrounded on the inside
        b1.hex, b2.hex = parse('0703'), parse('0704')
        e.units['r1'].hex = None
        e.units['r1'].status = 'dead'
        e.changed()
        steps = r2.steps
        e.resolve(r2.hex, [b1, b2], [], roll=6)
        self.assertLess(r2.steps, steps)

    def test_bombard_cannot_hurt_attacker(self):
        e = self.e
        e.end_phase()
        ba = e.units['bA']
        ba.hex = parse('0503')
        e.changed()
        r1 = e.units['r1']
        self.assertEqual(e.supporters_for(r1.hex), [ba])
        res = e.resolve(r1.hex, [], [ba], roll=1)
        self.assertEqual(res['alost'], 0)
        self.assertTrue(ba.fired)

    def test_out_of_ammunition(self):
        """CAN_SUPPORT keeps a gun from firing."""
        e = self.e
        e.end_phase()
        ba = e.units['bA']
        ba.hex = parse('0503')
        e.changed()
        e.d.CAN_SUPPORT = lambda eng, u: u.id != 'bA'
        try:
            self.assertEqual(e.supporters_for(e.units['r1'].hex), [])
            self.assertFalse(e.can_support(ba))
        finally:
            del e.d.CAN_SUPPORT

    def test_combat_sounds(self):
        """A fight sounds like the first unit's own fight, a barrage
        booms, and the rest is the game's COMBAT_SOUND or gunfire."""
        e = self.e
        b1, ba = e.units['b1'], e.units['bA']
        self.assertEqual(e.combat_sound([b1], []), 'gun')
        self.assertEqual(e.combat_sound([], [ba]), 'boom')
        e.d.COMBAT_SOUND = 'swords'
        try:
            self.assertEqual(e.combat_sound([b1], [ba]), 'swords')
            ba.spec['fight'] = 'bow'
            self.assertEqual(e.combat_sound([], [ba]), 'bow')
        finally:
            del e.d.COMBAT_SOUND
            del ba.spec['fight']

    def test_sequence_and_reinforcements(self):
        e = self.e
        self.assertEqual((e.turn, e.side, e.phase), (1, 'b', 'move'))
        e.end_phase()
        e.end_phase()
        self.assertEqual((e.turn, e.side, e.phase), (1, 'r', 'move'))
        self.assertEqual(e.units['r3'].status, 'pending')
        e.end_phase()
        e.end_phase()
        self.assertEqual((e.turn, e.side), (2, 'b'))
        e.end_phase()
        e.end_phase()
        self.assertEqual(e.units['r3'].status, 'map')
        for _ in range(20):
            e.end_phase()
        self.assertTrue(e.over)
        self.assertTrue(e.result)

    def test_supply(self):
        e = self.e
        self.assertIn(e.units['b1'].hex, e.supplied('b'))
        # a blue unit behind the red line is cut off
        b1 = e.units['b1']
        b1.hex = parse('0806')
        e.units['r3'].status = 'dead'
        e.units['r2'].hex = parse('0805')
        e.changed()
        self.assertNotIn(b1.hex, e.supplied('b'))

    def test_save_and_load(self):
        e = self.e
        b1 = e.units['b1']
        e.move(b1, parse('0303'))
        e.end_phase()
        d = e.to_json()
        e2 = Engine(util.tiny())
        e2.from_json(d)
        self.assertEqual(e2.units['b1'].hex, parse('0303'))
        self.assertEqual((e2.turn, e2.phase), (e.turn, e.phase))
        self.assertEqual(e2.rng.random(), e.rng.random())

    def test_fog(self):
        e = Engine(util.tiny(FOG=True), seed=1)
        vis = e.visible('b')
        self.assertIn('b1', vis)
        self.assertNotIn('r2', vis)
        self.assertEqual(e.visible(None), {u.id for u in e.alive()})

    def test_spot_hook(self):
        """SPOT(engine, spotter, unit, spot) sets how far each unit is
        seen: here the red units east of column 7 stand in the light."""
        lit = lambda e, v, u, spot: 9 if u.hex[0] >= 6 else 0  # noqa
        e = Engine(util.tiny(FOG=True, SPOT=lit), seed=1)
        vis = e.visible('b')
        self.assertIn('r1', vis)                # 0703, in the light
        self.assertIn('r2', vis)
        self.assertNotIn('b1', e.visible('r'))  # blue is in the dark

    def test_ai_plays_by_the_rules(self):
        """Two computer players finish the tiny game without an illegal
        move."""
        from grognard import play_out
        for seed in range(3):
            e = play_out(util.tiny(), seed=seed)
            self.assertTrue(e.over)

    def test_ai_attacks_good_odds(self):
        e = self.e
        e.end_phase()
        b1, b2 = e.units['b1'], e.units['b2']
        r2 = e.units['r2']
        r2.steps = 1
        b1.hex, b2.hex = parse('0805'), parse('0705')
        e.changed()
        act = AI(e, 'b', seed=1).next_action()
        self.assertEqual(act[0], 'attack')
        self.assertEqual(act[1], r2.hex)


class FastRules(unittest.TestCase):
    """The optional rules: ranged fire, a second move, disabled results,
    overruns, no zones of control, exits by type and unit values."""

    def setUp(self):
        d = util.tiny(
            RANGED=True, OVERRUN=True, ZOC=False,
            PHASES=['move', 'combat', 'move2'],
            CRT={'columns': ['1:1', '2:1'],
                 'rows': [['D', 'X']] * 6},
            EXITS={'r': dict(hexes=['E'], vp=5, types=['truck'])},
            UNIT_TYPES={'truck': dict(name='Truck', move='wheel')})
        d.UNITS = [dict(u) for u in d.UNITS]
        d.UNITS[0].update(range=3, m2=2, vp=2)          # b1 shoots far
        d.UNITS[3].update(vp=3)                         # r1 is worth 3
        d.UNITS.append(dict(id='rt', side='r', type='truck', a=0, d=1, m=4,
                            steps=1,
                            hex='0706'))
        self.e = Engine(d, seed=1)

    def test_ranged_fire(self):
        e = self.e
        e.end_phase()
        b1, r1 = e.units['b1'], e.units['r1']
        b1.hex = parse('0403')                  # three hexes from r1
        e.changed()
        self.assertEqual(distance(b1.hex, r1.hex), 3)
        self.assertIn(b1, e.attackers_for(r1.hex))
        self.assertNotIn(e.units['b2'], e.attackers_for(r1.hex))

    def test_disabled_then_destroyed(self):
        e = self.e
        e.end_phase()
        b1, r1 = e.units['b1'], e.units['r1']
        b1.hex = parse('0701')                  # two hexes off: 1:1
        e.changed()
        res = e.resolve(r1.hex, [b1], [], roll=1)
        self.assertEqual(res['result']['text'], 'D')
        self.assertTrue(r1.disabled and r1.alive)
        self.assertEqual(res['alost'], 0)
        # red's turn: r1 can't move or fire, then it recovers
        e.end_phase()               # blue: combat -> second move
        self.assertEqual(e.phase, 'move2')
        self.assertEqual(b1.mp, 2)
        self.assertEqual(e.units['b2'].mp, 0)   # no second move for it
        e.end_phase()
        self.assertEqual(e.side, 'r')
        self.assertEqual(r1.mp, 0)
        self.assertFalse(e.can_attack(r1))
        for _ in range(3):
            e.end_phase()
        self.assertEqual(e.side, 'b')
        self.assertFalse(r1.disabled)
        # disabled twice is destroyed, and its value goes to blue
        r1.disabled = True
        b1.attacked = False
        e.end_phase()
        bonus = e.bonus['b']
        e.resolve(r1.hex, [b1], [], roll=1)
        self.assertFalse(r1.alive)
        self.assertEqual(e.bonus['b'], bonus + 3)

    def test_no_zones_of_control(self):
        e = self.e
        self.assertEqual(e.enemy_zoc('b'), set())

    def test_overrun(self):
        e = self.e
        b2, r1 = e.units['b2'], e.units['r1']
        b2.hex = parse('0702')                  # next to r1, on clear
        e.changed()
        r = e.reachable(b2)
        self.assertIn(r1.hex, r.overruns)
        e.move(b2, r1.hex)
        res = e.last_overrun
        self.assertTrue(res['overrun'])
        self.assertTrue(b2.attacked)
        self.assertEqual(b2.mp, 0)
        if res['vacated']:
            self.assertEqual(b2.hex, parse('0703'))
        else:
            self.assertEqual(b2.hex, parse('0702'))

    def test_exits_by_type(self):
        e = self.e
        for _ in range(2):
            e.end_phase()
        e.end_phase()               # red moves now
        rt, r2 = e.units['rt'], e.units['r2']
        self.assertEqual(e.side, 'r')
        rt.hex = parse('0806')
        r2.hex = parse('0805')                  # on the edge too
        e.changed()
        e.end_phase()
        self.assertEqual(rt.status, 'exited')
        self.assertEqual(r2.status, 'map')      # only trucks leave
        self.assertEqual(e.bonus['r'], 5)

    def test_ai_plays_the_fast_rules(self):
        from grognard import play_out
        for seed in range(3):
            self.assertTrue(play_out(self.e.d, seed=seed).over)


class WallsAndOrders(unittest.TestCase):
    """Stone walls shift attacks made across them; units can be held
    until a turn."""

    def setUp(self):
        d = util.tiny(RIVERS=[('wall', ['0603/0703', '0602/0703'])])
        d.UNITS = [dict(u) for u in d.UNITS]
        d.UNITS[1].update(release=2)                    # b2 waits a turn
        self.e = Engine(d, seed=1)

    def test_wall(self):
        e = self.e
        e.end_phase()
        b1, b2, r1 = e.units['b1'], e.units['b2'], e.units['r1']
        b2.attacked = False
        b1.hex = parse('0603')
        e.changed()
        o = e.odds(r1.hex, [b1])
        self.assertIn((-1, 'stone wall'), o['shifts'])
        # one attacker not behind the wall: no shift
        b2.hex = parse('0702')
        e.changed()
        o = e.odds(r1.hex, [b1, b2])
        self.assertNotIn((-1, 'stone wall'), o['shifts'])
        # and crossing it costs a point more
        self.assertEqual(e.enter_cost(b1, parse('0603'), parse('0703')),
                         1 + 1 + 1)         # hills, and the wall

    def test_held(self):
        e = self.e
        b2 = e.units['b2']
        self.assertTrue(e.held(b2))
        self.assertEqual(b2.mp, 0)
        self.assertEqual(e.reachable(b2), {})
        for _ in range(4):
            e.end_phase()
        self.assertEqual(e.turn, 2)
        self.assertFalse(e.held(b2))
        self.assertEqual(b2.mp, b2.max_mp)


def production(**changes):
    """The tiny scenario with production: a yard that builds infantry
    for 4, an income of 3 a turn, an order that digs a unit in, and a
    third side that never moves (natives), dealt out by SETUP."""
    def setup(e):
        e.spawn(dict(id='n1', side='n', type='infantry', a=0, d=2, m=0,
                     hex='0501'))
        e.flags['setup'] = True

    def dig(e, u, key):
        u.spec['dug'] = True

    d = util.tiny(
        SIDES=util.tiny().SIDES + [dict(id='n', name='Natives',
                                        colour='#60a060')],
        ORDER=['b', 'r'], BRIEFING=False, SETUP=setup,
        TREASURY={'b': 5},
        UNIT_TYPES={'yard': dict(name='Yard', factory=True, move='foot',
                                 under=True, stack=0)},
        INCOME=lambda e, side: 3,
        BUILDS={'inf': dict(name='Infantry', cost=4, unit=dict(
            type='infantry', a=2, d=2, m=3))},
        ACTIONS=lambda e, u: [('Dig in', 'dig', None if u.kind ==
                               'infantry' else 'only infantry')],
        ACT=dig)
    d.UNITS = d.UNITS + [dict(id='byard', side='b', type='yard', a=0, d=2,
                              m=0, hex='0102')]
    for k, v in changes.items():
        setattr(d, k, v)
    return d


class Production(unittest.TestCase):
    def test_income_and_building(self):
        e = Engine(production(), seed=1)
        self.assertEqual(e.treasury['b'], 5 + 3)        # paid on turn 1
        self.assertEqual(e.build_sites('b'), [parse('0102')])
        self.assertIsNone(e.build_reason('inf', parse('0102')))
        self.assertIsNotNone(e.build_reason('inf', parse('0103')))
        u = e.build('inf', parse('0102'))
        self.assertEqual((u.side, u.hex, u.mp), ('b', parse('0102'), 3))
        self.assertEqual(e.treasury['b'], 4)
        self.assertIsNotNone(e.move(u, parse('0202')))  # moves at once
        self.assertIsNotNone(e.build('inf', parse('0102')))
        self.assertEqual(e.build_reason('inf', parse('0102')), 'costs 4')
        e.treasury['b'] = 10
        e.end_phase()                       # no building in combat
        self.assertIsNotNone(e.build_reason('inf', parse('0102')))
        # only blue reads what it built
        self.assertIn('Infantry built at 0102.', e.log('b'))
        self.assertNotIn('Infantry built at 0102.', e.log('r'))

    def test_spawned_units_saved(self):
        e = Engine(production(), seed=1)
        u = e.build('inf', parse('0102'))
        e.move(u, parse('0202'))
        d = e.to_json()
        e2 = Engine(production(), seed=2)
        e2.from_json(d)
        self.assertEqual(e2.units[u.id].hex, parse('0202'))
        self.assertEqual(e2.treasury, e.treasury)
        self.assertEqual(sorted(e2.units), sorted(e.units))

    def test_actions(self):
        e = Engine(production(), seed=1)
        b1 = e.units['b1']
        self.assertEqual(e.actions(b1), [('Dig in', 'dig', None)])
        self.assertTrue(e.act(b1, 'dig'))
        self.assertTrue(b1.spec.get('dug'))
        self.assertFalse(e.act(e.units['byard'], 'dig'))
        self.assertEqual(e.actions(e.units['r1']), [])  # not its turn

    def test_natives_and_no_briefing(self):
        e = Engine(production(FOG=True), seed=1)
        self.assertTrue(e.flags['setup'])
        self.assertEqual(AI(e, 'b').memory, {})
        # natives are everybody's enemy, and never take a turn
        self.assertIn('n', e.enemies('b'))
        for _ in range(6):
            self.assertIn(e.side, ('b', 'r'))
            e.end_phase()
        # the computer plays the game with them in it
        from grognard import play_out
        self.assertTrue(play_out(production(), seed=2).over)

    def test_worlds_lose_last(self):
        """A unit that's 'under' (a world beneath its fleet) takes its
        losses after the others in its hex."""
        e = Engine(production(), seed=1)
        yard = e.units['byard']
        u = e.build('inf', parse('0102'))
        e.take_losses([yard, u], 1)
        self.assertEqual((yard.steps, u.steps), (2, 1))


if __name__ == '__main__':
    unittest.main()
