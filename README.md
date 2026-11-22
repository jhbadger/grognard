# Grognard

An engine for *hex-and-counter wargames*, the kind played on a paper map
of hexagons with cardboard counters for regiments and battalions: zones
of control, stacking, a combat results table, supply lines, reinforcements
by turn and victory points for the towns that matter. It's written in
Python and Tk with nothing to install, and everything (the map, the
counters, the icon, the sound) is drawn in code, so there are no image or
sound files. The computer can play either side, or both; two people can
play at one screen.

It's a sibling of the [tilerpgs](../tilerpgs) and of
[blobber](../blobberrpg), and is built the same way: the whole screen is
drawn into one framebuffer in pure Python, and the front end only shows
the result, so a Kivy front end for Android is a few dozen lines. The one
exception is text: the window draws it over the picture in a real font,
so it stays smooth however big the window is (View, Text: pixels brings
back the bitmap font).

There are six games so far: a Second World War battle, a raid in a
far-future war of hovercraft and missile tanks that uses the engine's
optional rules for fast mechanized combat, the most famous charge of the
American Civil War, the storming of Chapultepec in the
Mexican-American War, a dawn rising in the streets of Belém in
Brazil's war of independence, and a battle at sea: Trafalgar.

```bash
./crossroads
```

```bash
./saltmarsh
```

```bash
./pickett
```

```bash
./chapultepec
```

```bash
./belem
```

```bash
./trafalgar
```

If Python reports `No module named '_tkinter'`, install your Python's Tk
package (`brew install python-tk` with Homebrew Python on macOS, or
`sudo apt install python3-tk` on Debian and Ubuntu).

## Crossroads: Bastogne, December 1944

The sample game. Seven roads meet at Bastogne, and the German offensive
in the Ardennes needs them all. The 101st Airborne Division and three
armoured teams of the 10th Armored must hold the town until Patton's 4th
Armored Division breaks through from the south.

- **Sixteen turns**, morning and afternoon from 19 to 26 December. The
  Germans move first each turn.
- **The map**: 26 by 20 hexes of snow, pine forest, villages, the road
  net, the railway to Gouvy, and the Sûre and Ourthe rivers.
- **The Germans**: the 2nd Panzer and Panzer Lehr divisions, the 26th
  Volksgrenadiers, the 5th Fallschirmjäger coming up from Wiltz, and the
  15th Panzergrenadiers on Christmas Eve.
- **The Americans**: the 501st, 502nd and 506th Parachute and the 327th
  Glider Infantry, Teams Desobry, Cherry and O'Hara, the remnants of the
  9th Armored, the 705th Tank Destroyers, the guns, and from the 22nd
  the 4th Armored Division.
- **The weather**: fog on the 19th; snow from the 21st, which slows
  everything off the roads; on the 23rd the sky clears, the 101st is
  supplied by air and American fighter-bombers shift every American
  attack a column.
- **Winning**: if the Germans hold Bastogne at the end of any turn they
  win at once. Otherwise the Germans score for the villages they take,
  American steps destroyed, and 2 VP a step for each unit they get off
  the western edge on the road to the Meuse; the Americans for German
  steps destroyed, Assenois, and holding Bastogne. The Germans must
  finish 11 VP ahead to win.

## Saltmarsh: a hover raid on the Iver Delta, 2187

The second game, and an original one. The Highland Directorate's hover
raiders come down out of the western hills onto the Iver Delta, a
drowned plain of salt marsh, tidal channels and saltpans crossed by one
causeway, to cut the Littoral Compact's convoys on the road north and
destroy its forward command post at Port Iver.

- **Twelve turns**, an hour each, through one night. The Directorate
  moves first.
- **Move, fire, move again**: each turn has a second movement phase after
  combat, and only skimmers (hovercraft) have a second move, so they can
  dash out of the marsh, shoot and slip back.
- **Fire at range**: every unit shoots out to its range (in brackets on
  the counter); missile tanks and mortars reach far. Results disable (no
  moving or firing next turn; a second disable destroys) or destroy;
  attackers never take losses.
- **Overruns**: in the first move a unit can drive into an enemy hex and
  fight there and then.
- **Terrain that favours the hovercraft**: skimmers cross water and
  marsh as easily as flats but can't enter the scrub woods; tanks can
  cross water only at the causeway's bridges; convoys keep to the road.
  There are no zones of control.
- **The Compact**: the command post, Bastion heavy tanks, Harpoon missile
  tanks, Petrel skimmers, mortar carriers, Delta Guard infantry dug into
  the villages, and four convoys coming up the road from the south.
- **The Directorate**: Kestrel skimmers, Corsair heavy skimmers, Javelin
  missile skimmers and Ram light tanks, in two waves.
- **Winning**: every unit is worth points to whoever destroys it (the
  command post 12, convoys 4), the Directorate scores the villages and
  Port Iver if it takes them, and the Compact scores 4 for each convoy
  off the north edge. The Directorate wins if it ends no more than 1 VP
  behind. Computer against computer it comes out about even.

The setting, the units, their numbers and the map are all new; the
mechanics are the genre's common stock, built into the engine so any
game can use them.

## Pickett's Charge: Gettysburg, 3 July 1863

The third game. Lee's last throw at Gettysburg: three Confederate
divisions against the centre of the Union line on Cemetery Ridge,
across nearly a mile of open fields, aiming for a copse of trees behind
a low stone wall.

- **Ten turns** of fifteen minutes, from two in the afternoon. The
  Confederates move first.
- **The cannonade**: for two turns the Confederate infantry wait in the
  woods of Seminary Ridge while their guns try to silence the Union
  batteries. Then Pickett's, Pettigrew's and Trimble's brigades go in,
  and Wilcox and Lang follow on the right. Bombardment is weak at long
  range (much of the real one went over the ridge), and once the
  infantry go the Confederate batteries are short of ammunition and fire
  only every other turn.
- **The field**: the fences along the Emmitsburg Road cost a point to
  climb; the stone wall, with its angle, shifts every attack made across
  it a column, the ridge another, and a battery in the hex attacked one
  more (canister). Brigades stack two to a hex and can lose three steps
  each.
- **The Union**: Gibbon's and Hays's divisions of the II Corps behind the
  wall, Stannard's Vermonters out in front on the left, Cushing's,
  Arnold's, Brown's and McGilvery's guns, Rittenhouse's on Little Round
  Top, and reinforcements from Hays's division, the Artillery Reserve
  and the VI Corps.
- **Winning**: the Confederates score the copse of trees (8), the Angle
  (6), Ziegler's Grove and Harrow's line (2 each) if they hold them at
  the end, and every Union step destroyed; the Union scores every
  Confederate step. The Confederates must finish 5 VP ahead. Computer
  against computer the Union holds a little more often than not, and
  the attackers lose about as many steps as the defenders, though they
  started with twice as many.

## Chapultepec: the storming of the castle, 12-13 September 1847

The fourth game. Scott's army has reached the edge of Mexico City; the
hill of Chapultepec and its castle, the Military College, stand between
it and the western gates.

- **Twelve turns**: the 12th in two halves, while the American siege
  guns bombard the castle and the infantry wait; then the 13th hour by
  hour from 8 in the morning. Worth's division joins at 10, and Santa
  Anna's reserves may come out of the city in the afternoon.
- **The storm**: the castle is a fortress (two columns, and its
  defenders lose a step rather than retreat), its north face a cliff
  that can't be climbed or attacked across; the slopes cost 2 and give a
  column; the cypress grove below has a wall round it. Storming the
  castle without one of the two storming parties, who carry the scaling
  ladders, costs another column.
- **The causeways**: east of the hill the meadows are flooded, 3 to
  enter and nothing on wheels, so the fight for the Belén and San Cosme
  gates is along two raised roads. Once the castle has fallen the
  defenders are shaken, and American attacks gain a column.
- **The armies**: Pillow's and Quitman's divisions, with the Voltigeurs
  and the Marines, Worth's division, the storming parties and the siege
  guns; against Bravo's garrison with the cadets of the Military
  College, the San Blas battalion, the gate garrisons and their guns,
  Álvarez's cavalry and Santa Anna's reserve.
- **Winning**: the castle and both gates is an American victory, the
  castle and one gate a marginal one (unless the Americans have lost
  more steps than they destroyed); the castle alone a marginal Mexican
  victory, and a castle that holds a clear one. Computer against
  computer the castle always falls, and the Americans force a gate a
  little more often than not.

## Belém: the rising of 14 April 1823

The fifth game, and the smallest: a morning's street fight between
companies. Brazil has declared its independence, but Grão-Pará, at the
mouth of the Amazon, stays loyal to Lisbon. A hundred conspirators meet
at João Baptista Balbi's house on the night of 13 April; at dawn they
take the artillery park and march to the Largo das Mercês to proclaim
Dom Pedro. The governor knew of the plot, and by full daylight his
colonels had the rebels surrounded.

- **Ten turns** of half an hour, from half past four in the morning.
  The Patriots move first. For the first two turns it's dark: units see
  only the next hex and every attack loses a column.
- **The city**: the Campina in the north, with the park, the Mercês and
  the barracks of the 3rd regiment; the Cidade Velha in the south, with
  the Forte do Castelo, the palace and the regiments' barracks; and the
  Piri swamp between them, crossed by the street along the river at
  the Ver-o-Peso or by going round its east end. Houses shift attacks a
  column, and so does the walled park; the palace and the fort two.
  Their defenders lose a step rather than retreat. Two companies to a hex in the
  streets.
- **The third regiment**: on each of turns 2 to 4 one of its companies
  turns out of its barracks, for the Patriots one time in four, plus
  one in four for each of the park and the Mercês they hold, less one
  if Loyalists stand next to the barracks; otherwise for the governor.
- **The Patriots**: Loureiro Barreto's men and the guns in the park,
  Boaventura Ferreira da Silva's soldiers and townsmen, Balbi's and Dias
  Cardoso's conspirators, Costa Rocha's men of the 3rd regiment and the
  crowd at the Mercês. At first light they lose a column attacking the
  regiments (Boaventura told his men to hold their fire).
- **The Loyalists**: the governor's guard, the fort's garrison and
  guns, Lieutenant-Colonel Nunes's gun, the 1st and 2nd regiments
  under Moura, Villaça and Barata (kept in barracks until turn 3), and
  sailors and a gun from the Arsenal.
- **Winning**: the palace or the fort in Patriot hands at the end is a
  Patriot victory (Pará declares for Dom Pedro four months early); the
  park and the Mercês both a marginal one; one of the two a marginal
  Loyalist victory, and neither (what happened) a Loyalist victory.
  Computer against computer the Patriots win about one game in four,
  always the marginal way.

The record of the rising is thin: who led it and roughly what happened,
but not the strength of the units or where in the city the park and the
barracks stood. The order of battle and the map are a reasonable guess
at a city of some twelve thousand people, not a survey.

## Trafalgar: Nelson's last battle, 21 October 1805

The sixth game, and the first at sea. Off Cape Trafalgar the Combined
Fleet of France and Spain, 33 ships of the line under Villeneuve,
straggles north towards Cádiz in a ragged crescent. Nelson's 27 ships
come down on it from the west in two columns, to break the line in two
places and fight it out ship against ship.

- **Thirteen turns** of half an hour, from 11:30 to 5:30. The British
  move first. Every counter is a ship, named, one to a hex: the
  Victory, the Royal Sovereign, the Santísima Trinidad, the Bucentaure,
  the Redoutable and the rest.
- **The wind** blows from the west. Sailing north-east or south-east,
  before it, costs 1 a hex; north or south, with the wind on the beam,
  1½; north-west and south-west, into it, can't be done. British ships
  move 3; the Combined Fleet, barely making steerage way, 1. A swell
  from 4:00 slows everyone. There are no zones of control: ships sail
  past one another, and through the gaps in the enemy line.
- **The fight**: ships next to each other fire, each once a turn, and
  several can gang up on one. Hits knock out steps; a ship that loses
  her last strikes her colours. A British ship firing from directly
  ahead of or astern of a Combined ship (the hex north or south of
  her) rakes her: a column. A British ship that didn't fire in her own
  turn is bow-on or turning and can't reply, so Combined attacks on her
  gain a column.
- **The fleets**: the British fire faster and harder (a British 74 is
  4-4, a French 74 3-3, a Spanish 2-3), but the French and Spanish ships
  are big and take a battering before they strike. Dumanoir's ten ships
  in the van wait for a signal until 1:30. The Africa comes down from
  the north on her own.
- **Winning**: the Combined ships taken, less two for each British ship
  lost. 18 or more (what Nelson got) is a decisive British victory, 16
  a British victory, 10 a marginal Combined victory, and fewer a
  Combined victory. Computer against computer the British win about
  three games in five.

The game starts with counters drawn as little ships; `P` switches to
NATO-style symbols.

## Playing

The screen is laid out like the wargames of the early '90s: a menu bar
on top, the map, a column of panels on the right (the date, the weather,
the score, the objectives and who holds them, the phase, and an arrow
pad), and a row along the bottom (the selected unit, the orders and the
log).

The screen fills the window. The window enlarges the game's pixels by a
step that keeps them crisp (1½, 2, 2½... times), and the game lays its
screen out at whatever size is left: the panels keep their size and the
map takes the rest, so a bigger window shows more of the map, and one
big enough moves up a step to bigger counters and text. A window taller
than it is wide gets the upright layout: the map on top and the panels
in columns underneath.

- **Moving**: tap one of your units; what it can't reach goes dark. Tap
  a lit hex to move there. Roads are quickest. Moving next to an enemy
  unit (into its *zone of control*) stops a unit, unless a friendly unit
  is already there, and a unit can't move straight from one enemy zone to
  another. Select a stack and all its units show in a strip in the corner
  of the map; tap one there (or the stack again) to pick it, or *Whole
  stack*.
  *Undo* takes back moves until you bump into the enemy.
- **Fighting**: enemy hexes you can attack are shaded red. Tap one and
  every unit that can join is outlined in green; tap your hexes to leave
  them out. Artillery joins from up to its range (in brackets on the
  counter), and the defender's guns in range help defend. The bottom
  panel shows the odds, the column shifts (terrain, rivers, armour in the
  open, air power) and what each roll of the die would do. *Attack!*
  rolls it. A city's defenders don't retreat: they lose a step instead.
  Win a hex and you may advance into it.
- **Steps**: most units can lose a step and fight on weaker (a pale band
  across the top of the counter); the last loss destroys them.
- **Supply**: a unit cut off from its side's map edges (by the enemy or
  their zones of control) gets a red corner: it moves at half speed and
  attacks at half strength.
- **Fog of war**: you only see enemy units near your own. Where you last
  saw them is marked with a faded counter and a `?`.

| Key | |
| --- | --- |
| Arrows, or drag the map | scroll |
| `+` `-` | zoom (three sizes, from the whole map to big counters with hex numbers) |
| `N` | next unit (or next target in combat) |
| `U` | undo a move |
| `E`, Space | end the phase |
| `A`, Enter | attack |
| `K` | the whole stack |
| `C` | find the selected unit |
| `T` | the combat results and terrain charts |
| `L` | the log |
| `G` | hex grid on or off |
| `P` | NATO symbols or pictures on the counters |
| Esc | cancel, or the menus |
| `?` | help |

The Options menu sets how well the computer plays (Easy, Normal, Hard),
how fast it moves, the sound, and which sides it plays. The game saves
itself to `~/.crossroads.json` at the start of every player turn and
when you quit; Continue on the title screen picks it up.

### Apps

```bash
./crossroads --build-app ~/Applications
```

writes `Crossroads.app` with the game's icon. It holds a copy of the game
and the engine and starts with the Python that built it.

```bash
./crossroads --build-android ~/crossroads-android
```

writes a Buildozer project for an Android app, with the same `build.sh`
(Docker) and `tar` as blobber and the tilerpgs. The app uses the Kivy
front end (`grognard/kivyshell.py`); `--kivy` runs that on the desktop
too, if Kivy is installed. Held upright, a phone gets the upright layout:
the map on top and the panels in columns underneath.

The APK is signed with a debug key kept in
`~/.android-keys/org.grognard.<game>/` (shared with blobber and the
tilerpgs, one folder per app), made by the game's first build and used by
every one after, so a new build installs over the old. Back that folder up: with a different key,
a phone won't take the new build without uninstalling the old one first.

## The engine

`grognard/` holds the engine, which knows nothing about any one game:

| Module | What it does |
| --- | --- |
| `hexgrid.py` | flat-topped hexes in columns (odd columns half a hex down), named `CCRR` as on a printed map; distances, neighbours, lines, rings, and the pixel shape of a hex at each zoom |
| `terrain.py` | the stock terrain, river and road tables, and the patterns they're painted with (grass, fields, trees, pines, hills, rough, marsh, water, villages, cities, snow) |
| `units.py` | units and unit types: NATO symbol, movement class, zone of control, armour, anti-tank, artillery |
| `rules.py` | the board, and the Engine: the sequence of play, movement, zones of control, stacking, supply, reinforcements, exits, combat, retreats, advances, victory points, fog of war, saving |
| `ai.py` | the computer player |
| `counters.py` | the counters: NATO symbols or little pictures, unit sizes, the numbers in a 3×5 font, reduced and out-of-supply marks |
| `render.py` | paints the whole map once per zoom: terrain, grid, terrain edges, rivers along hexsides, roads and railways |
| `view.py` | the map on screen: scrolling, zoom, units, highlights, flags, names |
| `widgets.py` | the panels, each a widget, and how they're laid out wide and upright at any size, and how big a screen a window gets |
| `game.py` | the menu bar, the modes (title, play, dialogs, menus, charts), input, animation, the computer's turns, saving and settings |
| `gfx.py`, `font.py`, `png.py` | the framebuffer, the bitmap font and PNG screenshots (from blobber) |
| `textfont.py` | the size of the smooth font the windows draw text in |
| `sound.py` | synthesized effects (blobber's players) |
| `tkshell.py`, `kivyshell.py` | the Tk and Kivy windows |
| `build.py` | the icon, the macOS app and the Android project |

### Text

The game lays out its text in its own pixels (640×480 at the least). When the window
can draw text itself (Tk and Kivy both can), the framebuffer doesn't draw
text into its pixels; it records each string, where it goes, its colour
and its shadow, and the window draws them over the scaled-up picture in
a real font (Tk's default font, Roboto on Kivy), sized so capitals are
about 7 of the game's pixels tall. The window also measures text for the
game, so wrapping and centring fit the font. A box drawn over recorded
text (a dialog over the map) hides it, as it would hide pixels. The
counters' tiny numbers stay pixels: they're part of the counter.
Screenshots (`--shot`) and the tests without a window use the bitmap
font. A game can choose a font with `FONT = dict(family='Georgia',
size=1.0, bold=False)`.

### The rules

The rules are the classic ones, and each part can be changed by a game:

- **Sequence**: each turn every side in `ORDER` has a player turn:
  reinforcements arrive, supply is traced, it moves, then it attacks.
  `ON_TURN(engine, side)` and `ON_END_TURN(engine)` hook in, and can
  keep their own state in `engine.flags`, a dict that's saved with the
  game.
- **Movement**: movement points, terrain costs by movement class, roads
  at their own cost (and over rivers: bridges), rivers adding to the cost
  of crossing (or forbidding it), weather multiplying costs off the
  roads. A unit may always move one hex if it hasn't moved. Entering an
  enemy zone of control ends a move; moving from one to another isn't
  allowed; friendly units cancel enemy zones where they stand.
  `ENTER_COST(engine, unit, a, b, cost)` can change the cost of any
  step, or forbid it with None (Trafalgar's wind).
- **Stacking**: `STACK` units a hex (HQs don't count), or the terrain's
  own `stack`.
- **Combat**: adjacent units attack one hex together, each once a turn,
  each hex once a phase. Artillery adds its strength from up to its
  range, or bombards alone (and can't be hurt doing so). Up to
  `DEFENSIVE_FIRE` (2) of the defender's guns in range add their
  strength to the defence against an assault (not a bombardment). Attacks across a river (`halve`) and by units
  out of supply are at half strength. The odds, rounded down, give a
  column of `CRT`; terrain `shift`s it (and an objective's own `shift`:
  fortifications), armour attacking into the `open` without anti-tank
  or armour defending shifts it one right, air power one right when the
  weather allows, and `COMBAT_SHIFTS(engine, hex, attackers, support)`
  adds any others. Results are step losses, retreats, exchanges and
  eliminations. Defenders who can't retreat stand and lose another step
  between them; in terrain that says `stand` (cities) they lose a step
  instead of retreating at all. Attackers may advance into an emptied
  hex.
- **Supply**: traced from `SUPPLY[side]['from']` (map edges `'N'`, `'S'`,
  `'E'`, `'W'` or hexes) up to `range`, through hexes free of the enemy
  and of their zones (unless friendly units hold them); roads count half.
  Out of supply: half movement, half attack. A weather's `airdrop` names
  a side that's supplied regardless.
- **Fog of war** (`FOG = True`): enemy units show within 2 hexes of your
  own (`spot`, 3 for reconnaissance), or 1 where they're in terrain that
  blocks sight (`los: False`), or in weather with its own `spot`; units
  that fought are seen for the rest of the turn.
- **Walls and fences**: a hexside kind with a `shift` (the stock
  `wall`, -1) shifts an attack when every unit attacking from next door
  comes across one; the stock `fence` (drawn with `posts`) only slows
  movement.
- **Held units**: a unit with `release` set to a turn sits where it is,
  not moving or attacking, until that turn (Pickett's infantry during
  the cannonade).
- **Optional rules for fast mechanized war** (Saltmarsh uses them all):
  - `PHASES = ['move', 'combat', 'move2']` adds a second movement phase
    after combat, for units with a second movement allowance `m2`;
    `PHASE_NAMES` renames phases.
  - `RANGED = True`: every unit attacks anything within its `range` (at
    least the next hex), not only its neighbours.
  - `OVERRUN = True`: in the first movement phase a unit can move into
    an enemy hex and attack it there, alone; if the hex is cleared it
    moves in, if not it stops next to it. Either way its move and its
    attack for the turn are spent. A type or unit with `overrun: False`
    can't.
  - `ZOC = False`: no zones of control.
  - Combat results `D` (disabled: no moving or attacking in the unit's
    next turn; disabled again, it's destroyed) and `X` (destroyed) for a
    game's own `CRT`.
  - A unit's `vp` is what destroying it is worth to the enemy, and
    `EXITS` can name the `types` that may leave (convoys).
- **Victory**: objectives held (each with `vp`, `owner` at the start, and
  `for`, the side it counts for), `STEP_VP` for each enemy step
  destroyed, `EXITS` for units leaving by an edge, and `SUDDEN_DEATH`
  hexes; `VICTORY(engine)` decides, returning (winner, words), or the
  side with more VP wins. `SCORE(engine, side)` sets what the panels
  show.

### The computer player

`ai.py` plays through the same Engine calls as a person, one action at
a time, so the screen shows each move. It sees only what its side can see,
remembering where it last saw each enemy unit (and it begins knowing the
enemy's starting positions, as the player does).

Moving, it first chooses garrisons for the objectives it must hold (the
strongest defenders in reach, as many as the danger calls for), then
scores every hex each unit can reach: closeness to the objectives it
wants to take or hold and to the exit edge; the terrain; supply; the
enemy strength that could reach the hex against the strength of the
stack there; and, for artillery, how many enemy hexes and held
objectives it would cover. Fighting, it works out the expected value of
every attack it could make (from the combat table's outcomes, weighing
steps lost on each side, retreats and ground taken), makes the best,
looks again, and stops when nothing is worth it.

With the fast rules it also weighs overruns among the places a unit can
move, keeps in range of targets rather than next to them, and after the
fight (the second move) thinks first of getting clear. Attacking sides
hunt enemy units worth 4 VP or more (Saltmarsh's convoys), and units
whose job is to leave the map (`EXITS` with `types`) head steadily for
the edge.

A side's `posture` ('attack' or 'defend') sets the balance; a unit can
have its own (the 4th Armored attacks while the rest of the Americans
defend), or one that starts on a given turn: `posture=('attack', 9)`.
Skill (Options) adds noise to its judgement and makes it settle for
worse odds.

```bash
./crossroads --simulate 20
```

plays 20 games between computer players and reports who won: a measure
of a scenario's balance (Crossroads comes out about even).

### Making a game

A game is a script that defines a handful of names and calls
`grognard.run()`. See `crossroads` for a complete one; `saltmarsh` for
one with the optional rules, its own unit types, NATO symbols drawn with
`@grognard.symbol`, counter pictures, terrain with a hovercraft movement
class, and its own panel colours; `pickett` for walls, fences, held
units, its own combat table, combat shifts and a turn hook (ammunition
running short), and its own font; `chapultepec` for a fortress
terrain, cliffs, a walled grove worked out in code, a side that gets
stronger when an objective falls, and victory decided by ground rather
than points; `belem` for units that join whichever side is
winning (two copies of each, one brought on by `ON_TURN`) and weather
that changes how far units see; and `trafalgar` for a game at sea:
ships on a map of open water, the wind worked out in `ENTER_COST`, its
own widget (the wind) and its own counter symbol and picture.

- `ID`, `TITLE`, `SUBTITLE`, `INTRO` (pages), `HELP` (pages added to the
  engine's), `ICON` (a function registered with `@grognard.icon`)
- `SIDES`: each a dict with `id`, `name`, `adj`, `colour` and `ink` for
  its counters, `posture` for the computer, and `about`, told to whoever
  plays it; `singular: True` for a name that takes a singular verb
  ("the Union takes the Angle")
- `ORDER`, `TURNS`, `START` (a date) and `TURN_PARTS` (`['AM', 'PM']`),
  or `TURN_NAME(turn)`
- `MAP`: rows of characters, one a hex, and `LEGEND` for any not in the
  stock one (`.` clear, `:` fields, `f` woods, `F` forest, `h` hills, `r`
  rough, `m` marsh, `t` town, `C` city, `~` water, space for off the map)
- `TERRAIN`, `HEXSIDES` and `ROAD_TYPES`: changes to the stock tables
  (each entry merged over the stock one)
- `ROADS`: `(kind, [waypoints])`, each leg running straight from one hex
  to the next
- `RIVERS`: `(kind, [sides])` for rivers, streams, walls and fences,
  each side `'0603/0703'` (between two hexes), `'1417:SW,S,SE'` (a
  hex's sides by direction) or a pair of hexes (`pickett` works its
  fences out in code)
- `LABELS`, `OBJECTIVES`, `SUDDEN_DEATH`, `EXITS`, `STEP_VP`, `VICTORY`,
  `SCORE`
- `UNITS` (see `units.py` for every field), with `hex` to start on the
  map or `arrive` and `at` to come later; `UNIT_TYPES` to add or change
  types
- `WEATHER` (by turn) and `WEATHER_TYPES`, `AIR` (who has air power),
  `SUPPLY`, `STACK`, `FOG`, `CRT`, `DEFENSIVE_FIRE`, `COMBAT_SHIFTS`
- `PANELS`: the widgets on the right and along the bottom (`date`,
  `weather`, `victory`, `objectives`, `phase`, `scroll`, `minimap`,
  `unit`, `orders`, `log`), and `CHROME`, their colours. A game can add
  widgets of its own with `@grognard.widget('name')`, terrain patterns
  with `@grognard.pattern('name')` and NATO symbols with
  `@grognard.symbol('name')`.
- `STYLE = 'pictures'` for little pictures on the counters instead of
  NATO symbols; `ZOOM` for the zoom a game starts at; `FONT` for the
  smooth text's font.

### Testing

```bash
./run_tests.py
```

runs the engine's tests (hex geometry, and the rules on a tiny scenario),
then each game's in its own Python: the map and units checked, computer
games played out, every screen and widget drawn wide and upright, a
player's moves, undo and attack through the screen, saving and loading,
a fuzz of random keys and taps, and the Tk window. `--long` fuzzes more,
`--no-gui` skips the window, and `KIVY_PYTHON` names a Python with Kivy
to test that window too.

```bash
./crossroads --selftest
```

checks the map, the units and the supply sources, draws every screen and
plays a computer game.

```bash
./crossroads --shot out.png --keys "new:us,enter,enter,enter,enter,enter,+"
```

plays a list of keys without a window and saves the screen as a PNG
(`new:SIDE` starts a game against the computer, `watch` one between
computers, `tap:X:Y` taps, `wait:N` lets N seconds pass). Other flags are
`--mute`, `--kivy` and `--scale 2`.
