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

There are twenty-five games so far: a Second World War battle, a raid in a
far-future war of hovercraft and missile tanks that uses the engine's
optional rules for fast mechanized combat, the most famous charge of the
American Civil War, the storming of Chapultepec in the
Mexican-American War, a dawn rising in the streets of Belém in
Brazil's war of independence, a battle at sea: Trafalgar, Far
Suns, a game of exploring, settling and conquering a cluster of stars,
where you build your own units, Tours, where the
Frankish foot stood against the horsemen of al-Andalus in 732, the
smallest: the Severn, a morning's fight in the woods of colonial
Maryland, sometimes called the last battle of the English Civil War,
Wisconsin Heights, Black Hawk's rearguard on the bluffs above the
Wisconsin River in 1832, Little Round Top, the fight for the left
of the Union line on the second day at Gettysburg, Maida, British
line against French column on a plain in Calabria in 1806, and the
oldest battle: Carrhae, where the Parthian horse archers shot Crassus's
legions to pieces in 53 BC, San Juan Hill, where Roosevelt and the
Rough Riders went up Kettle Hill outside Santiago de Cuba in 1898, and
Rorke's Drift, a company of the 24th Foot behind a wall of mealie bags
against the Zulu reserve on the night of Isandlwana, and Pegasus Bridge,
the glider-borne company holding the bridges over the Caen Canal and the
Orne in the first hours of D-Day, and Drvar, the SS parachute raid on
Tito's headquarters in the mountains of Bosnia in May 1944, and
the Fulda Gap, a Soviet attack in November 1983 that never happened,
and one that never could have: Nightspire, men, elves and dwarves
storming a witch-king's citadel against orcs, trolls, the walking dead
and a spell that turns regiments into sheep, and Hastings, Harold's
shield wall on its ridge against William's archers and knights in
1066, and Agincourt, Henry V's archers behind their stakes and the
French men-at-arms struggling toward them through the mud in 1415,
and Cowpens, Daniel Morgan's trap for Tarleton in 1781, and Tanga,
where an Indian army landing in German East Africa in 1914 was beaten
by the askari and by swarms of bees, and Nagashino, the Takeda horse
charging Nobunaga's matchlocks behind their palisade in 1575, and
Belleau Wood, the Marines crossing the wheat into the machine guns in
June 1918.

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

```bash
./farsuns
```

```bash
./tours
```

```bash
./severn
```

```bash
./heights
```

```bash
./roundtop
```

```bash
./maida
```

```bash
./carrhae
```

```bash
./sanjuan
```

```bash
./rorkes
```

```bash
./pegasus
```

```bash
./drvar
```

```bash
./fulda
```

```bash
./nightspire
```

```bash
./hastings
```

```bash
./agincourt
```

```bash
./cowpens
```

```bash
./tanga
```

```bash
./nagashino
```

```bash
./belleau
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

## Far Suns: exploration and conquest among the stars

The seventh game, an original one, and the first where you build your
own units. Two empires, the Concord and the Kesh, each begin on a
homeworld somewhere in a cluster of forty suns, and neither knows
where the other is.

- **Forty turns**, the Concord moving first. The cluster is the same
  every game, but what circles each sun is dealt afresh, and so are the
  homeworlds: two of eight places far apart, so you don't know which
  way the enemy lies.
- **The stars**: yellow and orange suns often have good worlds, red
  dwarfs and blue giants mostly ice and bare rock. A world is a garden,
  ocean, jungle, desert, ice world or barren rock, with room for 2 to 8
  billion people and some ore. A star is explored once a ship of yours
  has passed next to it (two hexes off, for a scout); a coloured dot by
  it shows its world, and the Star panel tells what you know. Nebulae
  cost 2 to cross, hide what's in them, and make it harder to hit.
- **Industry**: every turn each of your worlds pays its people and its
  ore, less the upkeep of your warships. Select a world of 3 people or
  more and *Build*: scouts, colony ships, escorts, cruisers,
  dreadnoughts (from a world of 6) and starbases, which guard a world
  and never move. New ships can move at once.
- **Settling**: a colony ship at a star with a free world can
  *Colonize* it: a colony of 1, growing by 1 every third turn up to
  what the world holds. At one of your colonies it can *Settle*,
  adding 1.
- **Natives**: many worlds are inhabited (mammals, birds, reptiles,
  sea-dwellers, insect hives, machines). Their star can't be entered
  until warships have pacified them; a colony on a pacified world
  starts with 2. They never attack, but fight back.
- **War**: there are no zones of control and no retreats; warships next
  to an enemy hex attack it together. A world loses people only once
  the ships over it are gone, and a world with enemy warships next to
  it is blockaded: it pays nothing, builds nothing and doesn't grow.
- **Winning**: take the enemy's homeworld (its last person) and you win
  at once. If neither falls, the empire with more people wins at the
  end. Computer against computer the two sides win about equally
  often, four games in five end with a homeworld taken, on turn 34 on
  average.

## Tours: between Poitiers and Tours, October 732

The eighth game. Abd al-Rahman al-Ghafiqi, governor of al-Andalus, has
raided over the Pyrenees, beaten Duke Odo of Aquitaine and sacked
Bordeaux, and his horsemen are riding north for the abbey of
Saint-Martin at Tours. On the old Roman road between the Clain and the
Vienne, Charles, mayor of the palace of the Franks, waits for them on a
wooded rise, his men on foot and shield to shield.

- **Ten turns** of an hour, from eight in the morning until dusk. The
  Umayyads move first. The Franks are hidden in the trees: units are
  seen within 2 hexes, 1 in woods, and at dusk only next door.
- **The field**: the two rivers close in to the north, so the horsemen
  can't ride round. The rise is slow going for horses; where it's
  wooded it gives the defenders a column. The fight is hand to hand,
  on a table of its own: a charge that doesn't break the line still
  costs the defenders a step as often as not.
- **Horse against foot**: almost all the Umayyads are mounted (the
  emir's guard, Arab horse of the Yemeni and Qaysi tribes, the Syrian
  junds and al-Andalus, and Berber light horse), and gain a column
  attacking into the open; but not against Charles's household, the
  Austrasian veterans and the Neustrians, spearmen in close order,
  and against them an attack by horsemen alone loses a column (the
  shield wall). The Frankish foot move only 2.
- **The camp**: on turn 4 Duke Odo's Aquitanian and Gascon horse ford
  the Clain in the south-west and go for the Umayyad camp and the
  plunder of Aquitaine. The first time a Frankish unit gets into the
  camp the plunder is scattered, for 6 VP. If Abd al-Rahman is killed,
  Umayyad attacks lose a column for the rest of the day; if Charles
  is, Frankish attacks do.
- **Winning**: the Umayyads score the crest (6) and Moussais (2) if
  they hold them at the end, a point for every step that rides off the
  north edge for Tours, and every Frankish step destroyed; the Franks
  the camp (8), the plunder, and every Umayyad step. Each leader is
  worth 4 more. The Umayyads must finish ahead. Computer against
  computer the Franks win a little more often than not (34 games in
  60, 15 of them clearly), and when Odo appears the emir
  and his best horse ride back to save the camp, as they did.

How the battle went is known only in outline, and its date, its place
and the size of the armies are all argued over. The order of battle and
the map follow the usual account (Moussais-la-Bataille, north of
Poitiers), not a survey.

## The Severn: Maryland, 25 March 1655

The ninth game. The Puritans of Providence, near present-day
Annapolis, have taken the government of Lord Baltimore's colony and
put out its governor, William Stone. Stone comes up the Chesapeake with
Baltimore's men and Piscataway allies, partly by land and partly in
boats, to take it back; the merchant ship Golden Lyon fires on his boats
and he lands on a wooded neck by the Severn. In the morning William
Fuller marches out to meet him under an English flag borrowed from the
ship. Both sides say they are loyal to Cromwell.

- **Ten turns** of a quarter of an hour. The Puritans move first,
  coming in from Providence to the west on the first two turns; Stone's
  force starts in the woods round its boats at the tip of the neck.
  Companies of twenty or thirty men, two to a hex, hidden in the woods
  until the enemy is next door.
- **Musketry** at close range, on a fire table of its own where even
  odds draw blood. The Puritan volley was far more effective: Puritan
  musketeers firing from the next hex gain a column. The Piscataway
  move through the woods as if they were open ground, and attacking
  them there costs a column.
- **The Golden Lyon** lies in the creek: her guns support Puritan
  attacks within 3 hexes and fire on attacks there. Stone's men can try
  to burn her from the shore (4 VP), but it takes most of his force.
- **Breaking**: at the start of its turn a side that has lost half its
  steps gives up (Stone orders his men to lay down their arms, or
  Fuller falls back on Providence), and so does Stone's force if Stone
  is down. Otherwise the score decides: the clearing, each step that
  gets down the path to Providence, the ship and Puritan steps for
  Stone; his boats, Stone himself and Stone's steps for the Puritans,
  who win ties. Computer against computer Stone wins a little over one
  game in four (17 in 60), and the Puritans, as in 1655, lose far fewer
  men than he does.

The record is two sets of partisan accounts that don't agree on much:
Stone had 130 men or 200 to 250, Fuller 100 to 170, and the hour isn't
known. The map and the companies are a guess, after the American
Battlefield Trust's account.

## Wisconsin Heights: the Black Hawk War, 21 July 1832

The tenth game. Black Hawk's "British Band" of Sauk and Meskwaki, about a
thousand people, most of them families, has fled for weeks through what
will be Wisconsin, starving, with the militia on its trail. At the
Wisconsin River the families build rafts and cross, while Black Hawk
and perhaps fifty to eighty warriors hold six or seven hundred mounted
volunteers under Henry Dodge and James D. Henry on the heights above.

- **Ten turns**: six of the day, two of dusk and two of night (the
  sources don't give the hour). The militia move first: Dodge's and
  Ewing's battalions on turn 1, Henry's three Illinois regiments on
  turns 2 and 3, with Ho-Chunk scouts already ahead.
- **The crossing**: the families of the band (lodge counters, which
  can't fight and have no zone of control) must get down through the
  river bottoms to the crossing. From turn 3, when the rafts are ready,
  each group that ends its move there goes over.
- **The rearguard**: the warriors move through woods, tall grass and up
  the heights at 1 a hex and see 3 hexes; the heights and the knoll
  give a column, and attacking warriors in woods or tall grass costs
  the militia another. Militia attacking with three battalions or more
  charge with the bayonet and gain a column. At night the militia,
  who put off their attack until morning, attack two columns worse,
  and before dawn Neapope calls out from the knoll in a language no
  one left with them understands.
- **Winning**: the Sauk score 4 for each group of the band that gets
  across and 2 for each militia step; the militia each warrior step, 4
  for each group of the band overtaken, Black Hawk (4), and the knoll
  and the crossing if they hold them at the end. Computer against
  computer the Sauk win 28 games in 60: about half the families get
  across, and the warriors lose six times as many steps as the
  militia.

The order of battle is simplified, and the map is a reasonable guess,
not a survey: the account it follows (Wikipedia's) gives the numbers
(600 to 750 militia, 50 to 80 warriors) but not the hour or the ground
in detail. Afterwards the band kept on to the Mississippi, where at Bad
Axe less than two weeks later hundreds of men, women and children were
killed.

## Little Round Top: Gettysburg, 2 July 1863

The eleventh game, and the second at Gettysburg, the day before
Pickett's Charge. Longstreet's attack on the Union left opens with
Hood's division going east from Warfield Ridge toward Devil's Den and
the two Round Tops. Little Round Top looks down the whole Union line,
and when the attack begins there is no one on it but the signal
station.

- **Twelve turns** of twenty minutes, from four in the afternoon. The
  Confederates move first. Regiments are the counters here, not
  brigades.
- **The race**: Law's Alabamians and Robertson's Texans and Arkansans
  go in at once, Benning's and Anderson's Georgians a turn later. Ward's
  brigade and Smith's battery hold Houck's Ridge and Devil's Den, with
  de Trobriand by the Wheatfield. Vincent's four regiments reach the
  hill on turn 2, O'Rorke's 140th New York and Hazlett's guns on turn 3,
  the rest of Weed's brigade on turn 4, and Crawford's Pennsylvania
  Reserves on turn 9.
- **The ground**: woods, boulders, slopes and the crest cost 2 to
  enter, Big Round Top 3, and Plum Run a point to cross. The boulders,
  woods, slopes and farms give the defender a column, the crest of
  Little Round Top two. Fog of war: in the trees and rocks you see a hex
  or two.
- **The 20th Maine**: from 6:00, with the enemy next to it, it's nearly
  out of ammunition and its next attack is Chamberlain's bayonet charge,
  two columns better. It charges once. Law's men, who had marched
  twenty-five miles and climbed Big Round Top without filling their
  canteens, attack a column worse on their own from 5:20.
- **Winning**: the Confederates score the summit (8), Hazlett's
  position and Vincent's Spur (3 each), Devil's Den (3), Houck's Ridge
  (2) and the Taneytown Road behind the hill (3) if they hold them at
  the end, and every Union step destroyed; the Union scores every
  Confederate step. The Confederates must finish 5 VP ahead. Computer
  against computer they win 29 games in 60, mostly by taking Devil's
  Den, Houck's Ridge or Vincent's Spur and wearing the Union down. The
  summit almost never falls, as it didn't in 1863.

The order of battle is simplified: most regiments are their own
counters, but Benning's, Anderson's, de Trobriand's and the
Reserves' brigades are one or two counters each, and the strengths are
set for play rather than counted from the returns. The map is drawn from
the battlefield's well-known landmarks, not surveyed.

## Maida: Calabria, 4 July 1806

The twelfth game. Joseph Bonaparte has been made King of Naples, and
Calabria is in revolt. General Stuart lands about five thousand British
and foreign troops in the bay of Sant'Eufemia to help it along, and
General Reynier, with about six thousand French, Poles and Swiss,
crosses the Lamato to drive them back into the sea. It's the classic
fight of the British line against the French column.

- **Ten turns** of twenty minutes, from eight in the morning. The
  French move first. Battalions are the counters: Compère's,
  Peyri's and Digonet's brigades, the 9th Chasseurs à cheval and a
  battery against Kempt's light battalion, Acland's, Cole's and
  Oswald's brigades and a few guns. The 20th Foot lands on the beach
  behind the British left on turn 4.
- **Line against column**: on open ground, when only infantry attack
  infantry, the French lose a column to the British volley and the
  British gain one (the volley, then the bayonet). The Chasseurs
  charging into the open gain a column, and the British have no
  cavalry. From ten o'clock the heat costs every attack a column.
- **The ground**: a flat plain with patches of myrtle scrub and olive
  groves between the sea and the heights of Maida. The Lamato behind
  the French costs 2 to cross and halves attacks across it, except at
  the ford.
- **Winning**: an army that has lost half its steps leaves the field at
  the start of its turn. Otherwise each side scores the enemy steps it
  destroys, the British the ford (5) and the French the beach at
  Sant'Eufemia (5). The British must finish 3 VP ahead to win.
  Computer against computer each side wins 30 games in 60.

In 1806 the French broke within minutes of the first volley and lost
perhaps a third of their men; the British lost a few hundred. The
victory thresholds are set so the game is even, not so it repeats
history. The order of battle is simplified, the strengths are set for
play, and the map is a reasonable guess at the ground, not a survey.

## Carrhae: Mesopotamia, 53 BC

The thirteenth game, and the oldest. Crassus, who shares the rule of
Rome with Pompey and Caesar, has marched seven legions into the open
plain east of the Euphrates. Surena meets him with nine thousand horse
archers, a thousand cataphracts and no infantry at all, and a train of
a thousand camels loaded with arrows.

- **Ten turns** of an hour, from noon. The Parthians move first. The
  Romans start in a square in the middle of the plain, and score each
  step that gets back to the gates of Carrhae at the north edge. Night
  falls at 8 PM: the Parthians can't shoot then and attack two columns
  worse.
- **Horse archers** shoot from 2 hexes away, alone or with the
  cataphracts, and can't be hurt doing it; they shoot into a Roman
  attack too. Each carries three volleys, and fills its quiver again
  at the start of the Parthian turn within 3 hexes of the camels.
  Take the camels and the arrows stop. By day, Roman foot entering a
  hex in range of a horse archer with arrows pays a point more, and
  Roman foot attacking only horse archers lose a column (they ride
  away).
- **The testudo**: a legion that neither moved nor fought in its last
  turn locks its shields, and arrows alone at it lose two columns. But
  cataphracts charging a legion in testudo gain a column, and charging
  anything else in the open gain one too.
- **Winning**: the Parthians score each Roman step, 2 more for each
  eagle (a legion destroyed), 3 for Publius Crassus and 5 for Crassus;
  the Romans each step that reaches Carrhae and each Parthian step.
  Publius's death costs the Romans a column, and Crassus's another.
  The Parthians must finish 10 VP ahead. Computer against computer
  each side wins 30 games in 60; the Romans get about half their
  steps to Carrhae.

It's an hour a turn and a legion a counter, so this is the battle much
simplified: the strengths are set for play, and the map is open plain,
the Balikh and Carrhae, not a survey. In 53 BC the Romans did reach
Carrhae in the night, leaving four thousand wounded behind, but Crassus
was killed at a parley a few days later and fewer than ten thousand
of his men got home.

## San Juan Hill: Santiago de Cuba, 1 July 1898

The fourteenth game. Shafter's V Corps comes down the one jungle road
from El Pozo toward Santiago, where Cervera's squadron lies in the
harbour. Between them stand the San Juan Heights, with a blockhouse on
San Juan Hill and Kettle Hill in front, and the San Juan River at the
end of the road. The Cavalry Division fights on foot, and among it are
the 1st US Volunteer Cavalry, the Rough Riders, and Lieutenant Colonel
Theodore Roosevelt, the only man on a horse.

- **Ten turns** of half an hour, from noon. The Americans move first.
  Regiments are the counters, and the Spanish battalions are in
  companies.
- **The ford**: the river can be crossed only at the Bloody Ford on
  the road, and from 12:30, when the balloon has found the trail to
  it, at a lower ford to the south. While the Spanish hold San Juan
  Hill, entering either bank of the Bloody Ford costs a point more.
- **The cavalry** starts across the river in the tall grass, held
  until the order to advance at 1:00. Hawkins's brigade is at the ford;
  Wikoff's arrives at 12:30, Pearson's and Parker's Gatlings at 1:00,
  and Bates's brigade from El Caney at 3:00. The Spanish get the
  Santiago volunteers at 1:30, Bustamante's sailors at 2:30 and the
  Asia battalion at 3:00.
- **Hell's Pocket**: at the start of each American turn every American
  unit in the open within 3 hexes of a Spanish rifle on the hills has a
  1 in 6 chance of losing a step to smokeless Mausers it can't see.
  Spanish attacks on Americans in the open gain a column.
- **Roosevelt** is a counter of his own. Attacking with other units he
  gains a column; he takes losses last, but if he's killed the Spanish
  score 5 VP and the Rough Riders attack a column worse. Parker's
  Gatlings support from 3 hexes and give an attack a column more.
- **Winning**: the Americans score San Juan Hill (8), Kettle Hill (4)
  and the north and south heights (3 each) if they hold them at the
  end, and every Spanish step; the Spanish every American step. The
  Americans must finish 4 VP ahead. Computer against computer they win
  30 games in 60: they take San Juan Hill most games, but lose about
  twice as many steps as the Spanish, as they did in 1898.

The order of battle is simplified and the strengths are set for play.
The map is drawn from the landmarks (El Pozo, the ford, the pond
between the hills, the blockhouse), not surveyed. Lawton's fight at El
Caney the same day is off the map.

## Rorke's Drift: Natal, 22-23 January 1879

The fifteenth game, and the smallest battlefield: a mission station by
the drift over the Buffalo River, a few acres a side. The afternoon the
Zulus destroy Chelmsford's camp at Isandlwana, their reserve, three or
four thousand men under Prince Dabulamanzi, comes on to the station.
Lieutenants Chard and Bromhead, with B Company of the 2nd/24th, a few
commissariat men and the sick, wall in the hospital and the storehouse
with mealie bags and biscuit boxes, and fight until dawn.

- **Twelve turns** of an hour, from 4:30 in the afternoon. The Zulus
  move first: the uDloko and inDluyengwe round Shiyane on turn 1, the
  uThulwana from the south-west on turn 2 and the inDlondlo from the
  north-west on turn 3, with riflemen in the caves of Shiyane. The
  British counters are sections of the company, Hook's men in the
  hospital, Dalton's commissariat men, the sick, and Chard and
  Bromhead. No fog of war.
- **The barricade**: the mealie bags round the station cost 2 to climb,
  and an attack made wholly across them is two columns worse; the line
  of biscuit boxes across the yard, one. The hospital and storehouse
  give a column more and their defenders lose a step rather than
  retreat. Chard or Bromhead in a hex costs a Zulu attack a column.
- **Volleys**: at the start of each Zulu turn every Zulu unit within 2
  hexes of a British section, outside the bush, loses a step on a 1 or
  2 (a 1 at night away from the firelight), at a box of cartridges a
  shot. There are 100 boxes; when they're gone, Zulu attacks gain a
  column. From 7:30 it's dark, and Zulu attacks away from the firelight
  lose a column.
- **The hospital**: from 6:30 a Zulu next to it sets the thatch alight.
  No one may go in after that, and British units still inside lose a
  step at the start of each Zulu turn. Once the Zulus reach the
  hospital, Hook and Williams cut through the walls and the sick are
  carried to the storehouse at the start of a British turn. The fire
  lights the ground for 4 hexes round.
- **Winning**: the Zulus score the storehouse (8), its door (3), the
  yard (3) and the kraal (2) if they hold them at dawn, 3 for every
  British step, 4 for the sick and 3 for each officer killed; the
  British score every Zulu step. The British must hold the storehouse
  and finish 3 VP ahead. Computer against computer the Zulus win 32
  games in 60. The kraal always falls, as it did; the storehouse
  hardly ever does, and the sick get out alive in nearly every game.

In 1879 the Zulus lost about 350 killed and the British 17. The strengths
are set for play, the counters are sections rather than men, and the
map is the station's few buildings and the ground round them as the
accounts describe it, not a survey.

## Pegasus Bridge: Normandy, 6 June 1944

The sixteenth game, and a small one: two bridges a few hundred yards
apart, over the Caen Canal at Bénouville and over the Orne, the only
way between the beaches and the 6th Airborne Division east of the
river. Just after midnight Major Howard's D Company of the Ox and
Bucks, with a party of sappers, lands beside them in six gliders and
takes both in minutes. The game begins with the codewords Ham and Jam
going out, and the company has to hold until relieved.

- **Fourteen turns** of an hour, from 12:30 in the morning to 1:30 in
  the afternoon. The Germans move first. The British counters are D
  Company's platoons, Sergeant Thornton's PIAT, the sappers and Howard
  himself; the 7th Parachute Battalion's companies come over the Orne
  from 2:30, and Lovat's No. 6 and No. 45 Commandos up the Colleville
  road at 12:30. The 21st Panzer Division's tanks and panzergrenadiers
  come up from Caen and in from the west from 1:30, the 716th
  Division's grenadiers down from Ouistreham at 4:30, assault guns at
  7:30, and von Luck's men up the east bank of the Orne from 5:30.
- **The bridges**: the canal and the river can be crossed only on
  them, and an attack over a bridge is at half strength. The canal
  bridge's objective is the Café Gondrée at its western end, where the
  defenders lose a step rather than retreat.
- **The night**: until 5:30 units see only the next hex and every
  attack is a column worse. Howard in a hex costs a German attack on it
  a column. The first commando over the canal bridge scores the British
  2 VP (Lovat apologises for being two and a half minutes late).
- **Winning**: each side scores the objectives it holds at the end (the
  canal bridge 10, the Orne bridge 6, Le Port and Bénouville 3 each)
  and every enemy step, Howard 3 more. The British must hold the canal
  bridge and finish 13 VP ahead. Computer against computer they win 31
  games in 60. The canal bridge almost never falls, as it didn't in
  1944; the game turns on the Orne bridge and the villages.

The German order of battle round the bridges that night is uncertain,
and the counters here (which companies, how many tanks, when they came)
are a guess set for play. The map is drawn from the landmarks (the
café, the T-junction, Le Port's church, the château), not surveyed,
and the strip between the canal and the river is wider than it was.

## Drvar: Bosnia, 25-26 May 1944

The seventeenth game, and a fight with partisans: Operation
Rösselsprung, the Knight's Move. At seven in the morning on Tito's
birthday the 500th SS Parachute Battalion comes down by parachute and
glider on Drvar, the little sawmill town that is the capital of the
Partisans' liberated territory, to take Tito dead or alive. He is in a
cave in the cliff across the Unac with his escort; the cadets of the
officers' school are up the road at Šipovljani, and the youth congress
has been celebrating his birthday in the town all night.

- **Fourteen turns**: an hour each from 7:00 AM to 3:00 PM, then three
  hours each through the night to 6:00 AM. The Germans move first.
  The paratroopers start on the map: five glider assault groups named
  for their targets and three parachute companies, with a second wave
  at noon. The Partisans have the escort, the town guard, the youth
  delegates and the cadets, and the 3rd Lika Brigade's battalions come
  in from 8:00, the 1st Proletarian and 5th Krajina Brigades at dusk
  and in the night. The German ground columns from Bihać and Petrovac
  arrive at dawn on the 26th.
- **Tito** is a counter of his own, held in the cave until 9:00, when
  the escort has cut a way out through its floor. If he's killed the
  Germans win at once; if he gets off the east edge, over the mountains,
  the Partisans score 8.
- **Day and night**: in daylight the Luftwaffe gives German attacks a
  column and drops them supplies. From dusk units see only the next
  hex, the Partisans gain a column attacking and the Germans lose one,
  and paratroopers cut off from the Petrovac road are out of supply.
  The cemetery's walls give its defenders two columns, and they lose a
  step rather than retreat. The Unac costs 2 to cross and halves an
  attack over it, except at the bridge.
- **Winning**: each side scores every enemy step destroyed and the
  places it holds at the end (Drvar 5, the cemetery 4, the cave 3,
  Šipovljani 2). The Germans must finish 1 VP ahead. Computer against
  computer they win 32 games in 60. Tito gets away in every one, as he
  did; a German player who pushes over the Unac at once may catch him.

The order of battle is simplified and the strengths set for play; the
assault groups' names and targets are as the accounts give them, but
which Partisan battalions came when is a guess. The map is the valley
as the accounts describe it (the town, the cemetery on its knoll, the
cave over the river, the road to Šipovljani), not a survey.

## Fulda Gap: Hesse, November 1983

The eighteenth game, and the first about a battle that wasn't
fought. In November 1983 NATO rehearsed the release of its nuclear
weapons in a command post exercise, Able Archer 83, and in Moscow some
took it for cover for a real first strike. Here they act on the fear:
on the night of 10 November the Group of Soviet Forces in Germany
attacks first, without nuclear weapons, through the Fulda Gap toward
Frankfurt, hoping to reach the Rhine before NATO decides to use its
own.

- **Twelve turns**, day and night from 11 to 16 November. The Soviets
  move first.
- **The map**: 26 by 18 hexes from the inner-German border on the east
  edge to the Wetterau on the west: the Seulingswald north of the gap,
  the Rhön south of it, the Vogelsberg, the Spessart, the city of Fulda
  behind the Fulda river, and the Kinzig valley down to Gelnhausen and
  Hanau.
- **The Soviets**: the 8th Guards Army. The 39th and 57th Guards Motor
  Rifle Divisions cross at Rasdorf and Tann on the first day, with the
  army's guns and Hinds and an air assault battalion already landed on
  the Fulda bridges; the 79th Guards Tank Division follows on the
  second day, the 27th Guards on the third, and a division of the 1st
  Guards Tank Army on the fourth. Counters are regiments.
- **NATO**: the three ground squadrons and the air cavalry of the 11th
  Armored Cavalry Regiment on the border, a Heimatschutz battalion in
  Fulda, and the 2nd Brigade of the 3rd Armored Division at Gelnhausen.
  The rest of the 3rd Armored, the V Corps artillery and the
  Bundeswehr's Panzerbrigade 14 come on the second turn, and the
  brigades of the 8th Infantry Division up the Kinzig from the fourth.
- **Helicopters**: the Cobras, the Blackhorse's air cavalry and the
  Hinds are support units that fly a point a hex over anything, add
  their strength to fights within two hexes, and don't fly at night or
  in fog.
- **Day and night**: on the first day the Soviets have surprise and the
  air, and every Soviet attack gains a column. At night units see only
  the next hex and Soviet attacks lose a column to NATO's thermal
  sights. On clear days after the first, the A-10s give NATO's attacks
  a column.
- **Winning**: if the Soviets hold Gelnhausen at the end of a turn, or
  get 4 steps off the west edge by the Kinzig valley, they win at once:
  the road to Frankfurt is open, and SACEUR asks for nuclear release.
  Otherwise each side scores the enemy steps it destroys and the towns
  it holds (Fulda 6, Gelnhausen 4, Bad Hersfeld and Schlüchtern 3, the
  rest 2), and the Soviets 3 VP a step they get off the west edge. The
  Soviets must finish 6 VP ahead. Computer against computer they win
  28 games in 60.

Everything here is a guess, since it never happened. The formations
are those of 1983 and in the places they were based, but the Soviet
regiments are numbered by division rather than by their real numbers,
the timing of each echelon is a planner's, not a historian's, and the
strengths are set for play. The map follows the country, not a survey.
The game stops at the nuclear threshold and doesn't go past it.

## Nightspire: the storming of the Witch-King's citadel

The nineteenth game, and a fantasy. For three hundred years Malgrith
the Witch-King has ruled the Ash Wastes from Nightspire, a black
citadel among dead mountains. Now his horde is over the Greywater and
on the road to Aldermere, and the men of Aldermere, the elves of
Silverwood and the dwarves of Ironhold march the other way to end him.

- **Twelve turns**, three days of dawn, day, dusk and night. The
  Alliance moves first. At night units see only the next hex and the
  dead gain a column attacking.
- **The map**: 24 by 14 hexes from Aldermere on the west edge to
  Nightspire in the east: Silverwood, where elves move freely, the
  Ironhills, where dwarves do, the Greywater and its bridge at
  Greyford, the Fenmire, the Barrows, the Black Tower and the Ash
  Wastes. Nightspire can be attacked from only three hexes.
- **The Alliance**: knights, men-at-arms, longbowmen and outriders of
  Aldermere; wardens, archers and riders of the elves; and from the
  second turn the dwarves' axes and crossbows, with a siege engine on
  the third. Archers support attacks from two or three hexes.
- **The Dark Host**: orc warbands and wolf riders, the Black Guard in
  the citadel, hill and cave trolls, a wyvern that flies over
  anything, skeleton legions, barrow-wights and dread riders.
- **Heroes**: Prince Aldric, Lady Elowen and Brokk Stonehelm against
  Malgrith, Uzgar, Vesska and Morrowgast. They don't count for
  stacking and can't attack alone; with an attacking unit they give
  their lead in columns (the Witch-King 2, the rest 1), and in a hex
  attacked they take it away. Brokk gives one more against walls.
- **Spells**: Malgrith, Vesska the hag and Morrowgast the lich each
  cast one spell a turn from a pool of power that comes back a point a
  turn. Sheep turns a regiment or a hero within three hexes into a
  sheep, on 4 or more (Malgrith 3, and one more near Elowen); Bolt
  takes a step; Raise brings up a band of skeletons. Sheep can't
  fight: the Dark Host scores 2 for each one it kills (4 for a hero)
  and the Alliance 1 for each it drives off the west edge, so sheep
  want an escort. If Malgrith dies his spells die with him, and every
  sheep left on the map is itself again.
- **Winning**: holding Nightspire, or for the Dark Host Aldermere, at
  the end of a turn wins at once. Otherwise each side scores enemy
  steps, places held (Aldermere and Nightspire 10), sheep and heroes;
  Malgrith is worth 10. The Dark Host must finish 10 VP ahead to win.
  Computer against computer it wins 33 games in 60. The end of the
  game tells what became of every hero who was turned into a sheep.

The world, its people and its numbers are all made up; the mechanics
are the engine's, with spells built on a game's own orders.

## Hastings: Senlac Hill, 14 October 1066

The twentieth game. Harold Godwinson has beaten the Norwegians at
Stamford Bridge and marched the length of England to meet William of
Normandy, who has landed at Pevensey. On a ridge across the London
road Harold forms his army in a wall of shields; below it the duke
forms his in three divisions, archers in front, foot behind and the
knights last. Harold has only to stand until dark.

- **Nine turns** of an hour, from nine in the morning until dusk. The
  Normans move first. Both armies are in full view.
- **The field**: the crest of the ridge costs 2 to climb (3 for
  horses) and gives the defenders a column; the slope below it is open
  ground, and the valley is boggy at both ends, where horses can't go.
  Round Harold's standard the king's household gives another column,
  and its defenders never give ground: driven back, they lose a step
  instead.
- **The shield wall**: housecarls and thegns cancel the knights' shock
  even in the open; knights alone lose a column attacking them, and so
  do archers shooting alone until 3 PM, when William orders them to
  shoot high.
- **The levies**: at the start of the English turn, thegns or levies
  next to a Norman unit that attacked and lost a step run down the hill
  after it one time in two (one in three with Harold or an earl beside
  them, two in three once Harold is dead). From noon any knights that
  attacked will do: they run away on purpose. Those that run are out of
  the line for the turn, and levies caught in the open give the knights
  a column.
- **Winning**: the day turns on the standard and the king. The
  standard in Norman hands at the end with Harold dead is a Norman
  victory, either one a marginal one; otherwise the English win,
  clearly if the Normans aren't ahead on points (the standard, the ends
  of the ridge, steps destroyed, and the king, the earls, the duke and
  the bishop). Computer against computer the Normans win 44 games in
  100.

The armies are guesses, as every account of them is, and the counters
are divisions of the army, not regiments. The map follows the usual
account (the ridge where Battle Abbey stands, Telham Hill to the
south), not a survey.

## Agincourt: Saint Crispin's day, 25 October 1415

The twenty-first game. Henry V has taken Harfleur and is marching his
sick and hungry army to Calais, and the army of France, three or four
times his number, is across the road. After a night of rain the armies
face each other across a ploughed field between the woods of Azincourt
and Tramecourt. Henry moves first: his line goes forward to bowshot,
and the archers hammer their stakes into the mud.

- **Eight turns** of half an hour, from 11 in the morning. The French
  move first. Both armies are in full view.
- **The field**: the ploughed field is deep mud, 2 to cross (3 for
  horses), and the woods close in toward the English so the French
  can't go round. Round the king's banner the English never give
  ground.
- **The archers** shoot from 2 hexes and can't be hurt doing it, and
  gain a column shooting into the mud; up to 3 of them shoot into every
  French attack, adding their strength to the defence. Stakes guard
  their front: an attack across them loses a column, and horsemen lose
  another and pay 4 to cross.
- **The French**: the vanguard on foot and the horse on its wings go
  forward at once; the main battle is held until turn 3, the mounted
  rearguard until turn 6, and the Duke of Brabant arrives late on
  turn 5. An attack by 4 units or more loses a column (the press), and
  so does one by men-at-arms who have all moved this turn and stand in
  the mud (winded). On turn 4 Ysembart d'Azincourt and the peasants of
  the village come out of the woods for the English baggage at
  Maisoncelle.
- **Winning**: the French score 2 for each English step destroyed,
  the king's banner (6) and Maisoncelle (4), and Henry (8), York,
  Gloucester and the baggage; the English score each French step and
  the great lords. The French must finish 10 VP ahead. Computer against
  computer each side wins 30 games in 60.

The French losses at Agincourt were in thousands and the English in
hundreds; here an English step is worth two French, and the strengths
are set for play. The map follows the usual reconstruction (the
French on the higher ground by the Calais road, the English between
the woods with Maisoncelle behind them), not a survey.

## Cowpens: South Carolina, 17 January 1781

The twenty-second game. Banastre Tarleton has marched all night to
catch Daniel Morgan's little army in a cattle pasture with the Broad
River at its back. Morgan has told his militia exactly what to do:
fire two volleys at the men with the epaulettes, then fall back behind
the Continentals on the rise.

- **Eight turns** of ten minutes from seven in the morning. The
  Americans move first. Units are seen within 2 hexes, 1 among the
  trees; Washington's horse waits out of sight behind the second rise.
- **Volleys**: riflemen (range 2) and Pickens's militia (range 1) don't
  attack; they fire into attacks like guns, and can't be hurt firing.
  Each has two volleys, and loads again at the start of the American
  turn if it's within 2 hexes of Morgan and not next to a British unit.
  Up to 2 fire into each British attack.
- **The trap**: from 7:40 the British have been marching for nearly
  five hours and attack a column worse. An American attack made from 3
  hexes or more gains a column. The 71st is held back until turn 3;
  Washington's horse turns to the attack on turn 5, the Continentals
  on turn 6.
- **Winning**: the British score the rise (6) and Morgan's post (3),
  American steps and Morgan; the Americans British steps, Tarleton and
  the guns. The British must finish 4 VP ahead. Computer against
  computer each side wins 30 games in 60.

The counters are battalions and detachments, the strengths set for
play, and the map is the pasture and its two rises as the accounts
describe them, not a survey.

## Tanga: German East Africa, 4 November 1914

The twenty-third game. Indian Expeditionary Force B has landed at Ras
Kasone to take the port of Tanga, the end of the Usambara railway.
Lettow-Vorbeck has a few companies of askari in the town and more
coming down the line by train, and between the beach and the town
there are rubber plantations, thick bush and wild bees.

- **Eight turns** of an hour from noon. The British move first.
  Plantations hide what's in them; the bush hides it too, costs 2 and
  gives the defenders a column; the railway cutting in front of the
  town gives one more. At dusk units see only next door.
- **The bees**: seven hives are hidden in the plantations and the bush,
  in different places each game. A unit that moves into one rouses it
  two times in three, and every unit in that hex and next to it, of
  either side, scatters for the rest of its turn and the next. The
  half-trained battalions lose a step one time in two.
- **The forces**: the 13th Rajputs, the 61st, the 63rd and the 98th
  lose a column attacking alone; the Loyal North Lancs and the
  Kashmiris gain one fighting in the town. The cruiser Fox shells
  anything within 3 hexes of her. German companies arrive by train
  from turn 2, machine guns fire into attacks on their neighbours, and
  from dusk every German attack gains a column.
- **Winning**: the British score Tanga (8) and the station (4) and
  German steps; the Germans British steps. The British must finish 5
  VP ahead. Computer against computer they win 32 games in 60.

The forces are close to the real ones, the strengths are set for play,
and the map is the peninsula between Tanga and Ras Kasone as the
accounts describe it, not a survey.

## Nagashino: Shitaragahara, 28 June 1575

The twenty-fourth game. Takeda Katsuyori has besieged the castle of
Nagashino, and Oda Nobunaga and Tokugawa Ieyasu have come to relieve
it. They dig in behind a palisade along the Rengo stream with
thousands of matchlock men behind it, and the Takeda horse must charge.

- **Eight turns** of an hour from six in the morning. The Takeda move
  first, across rice paddies (2, 3 for horses) and the stream. The
  palisade runs the length of the field: an attack across it loses a
  column, horsemen lose another, and horses pay 4 to cross.
- **The guns** fire from next door and can't be hurt doing it, and up
  to 2 fire into each Takeda attack; but a gun that fires must reload.
  One that fired in the allies' turn can't fire into the next Takeda
  attack, and one that fired into an attack can't fire in the allies'
  next turn. The guns and the spearmen don't leave the palisade;
  spearmen cancel the horses' shock.
- **The castle and the raid**: Nagashino gives its defenders two
  columns and never gives ground. On turn 2 Sakai Tadatsugu's raiders
  come out of the hills behind the Takeda for the forts at Tobigasu.
  When three of the six old generals are dead, or Katsuyori, the Takeda
  attack a column worse.
- **Winning**: the Takeda score Nobunaga's and Ieyasu's camps, the
  castle, allied steps and the two commanders; the allies Takeda
  steps, Tobigasu, the generals and Katsuyori. The Takeda must finish 2
  VP ahead. Computer against computer they win 28 games in 60: either
  they break a hex of the palisade and ride for the camps, or the
  charge dies in front of it.

How the guns were fired at Nagashino (in three ranks, or not) is
argued over; the game's rule is only that a gun can't fire twice
running. The strengths are set for play, and the map is
Shitaragahara as the accounts describe it, not a survey.

## Belleau Wood: the Marne, 6 June 1918

The twenty-fifth game. The German spring offensive has reached the
Marne. The 4th Marine Brigade has stopped it in front of Lucy-le-Bocage,
and on 6 June it attacks: Hill 142 at dawn, and in the evening the
wood itself and the village of Bouresches, across open wheat.

- **Ten turns** of two hours from four in the morning. The Marines
  move first. The wood is dense trees and boulders: 2 to enter, a
  column to its defenders (two among the boulders), and nothing in it
  is seen from more than next door. At dawn, dusk and night units see
  only next door.
- **The wheat**: by daylight a Marine unit that moves through wheat
  within 2 hexes of a German machine gun loses a step one time in
  three. Machine guns fire from 2 hexes and can't be hurt doing it, and
  up to 2 fire into each attack. Marines attacking anything in the open
  gain a column (aimed rifle fire).
- **The day**: two battalions of the 5th Marines go for Hill 142 at
  dawn; the three for the evening attack are held until 4 PM. German
  reserves come down from the north at dusk, and by night German
  attacks gain a column.
- **Winning**: the Marines score Hill 142 (4), Bouresches (6) and the
  south (4) and north (6) of the wood, and German steps; the Germans
  Marine steps. The Marines must finish 10 VP ahead. Computer against
  computer they win 27 games in 60.

It took the Marines until 26 June to clear the wood; this is only the
first day. The battalions are the real ones, the strengths are set for
play, and the map follows the ground, not a survey.

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
  game. If `ON_END_TURN` ends the game, `SUDDEN_DEATH` isn't looked at.
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
  strength to the defence against an assault (not a bombardment).
  `CAN_SUPPORT(engine, unit)` can keep a gun from firing at all (out of
  arrows, in the dark). Attacks across a river (`halve`) and by units
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
  show; `HIDDEN_SCORE = True` shows the player only their own until
  the end.
- **Production** (Far Suns uses it): each side has a treasury
  (`TREASURY` at the start), and `INCOME(engine, side)` is added to it
  at the start of its turn. `BUILDS` names what can be built: each a
  dict with `name`, `cost`, `about` and `unit`, the unit's spec. In
  the first movement phase a side builds at its yards (any unit whose
  type says `factory`, or `BUILD_SITES(engine, side)`), unless
  `CAN_BUILD(engine, side, kind, hex)` gives a reason not to; the
  orders panel shows *Build...* when a unit at a yard is selected, and
  the `treasury` widget the money and the income. Built units can move
  at once; `ON_BUILD(engine, unit)` can name them.
- **Units made in play**: `engine.spawn(spec)` puts a new unit on the
  map, and saves keep it; `SETUP(engine)` is called once at the start
  of a new game to deal out a map afresh (Far Suns' worlds and
  homeworlds, using `engine.rng`), and `engine.remove(unit)` takes one
  off without a fight.
- **A game's own orders**: `ACTIONS(engine, unit)` gives the active
  side's unit buttons, `[(label, key, why not)]` (`why not` None when
  it can), and `ACT(engine, unit, key)` carries one out (Colonize,
  Nightspire's spells). `ACT` can add `('sound', name)` and
  `('popup', hex, text, colour)` to `engine.events` for the screen.
- **Sides that never move**: a side in `SIDES` but not in `ORDER` has
  no turns and no player (Far Suns' natives); its units are everyone's
  enemy. `BRIEFING = False` keeps each side from knowing where the
  other starts.
- **Hooks**: `ON_MOVE(engine, unit, path)` after every move (exploring),
  `ON_ELIMINATE(engine, unit, hex)` when a unit is destroyed (a
  homeworld falling ends the game), and `engine.say(text, side)` for a
  line in the log only that side reads.

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

Far Suns has its own computer player (`Strategist`, in the game's
script): it builds what it lacks (scouts while there are stars to
explore, colony ships while there are free worlds, warships while
there's income to keep them), sends scouts to the nearest unexplored
stars and colony ships to the best worlds for the trip, and gives its
warships missions: defend the homeworld, then, once it's strong
enough, take the enemy's; defend colonies, raid the enemy's, and
pacify the natives on the best worlds. A fleet gathers two hexes from
its target, where it can see what's there, and goes in together.

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
that changes how far units see; `trafalgar` for a game at sea:
ships on a map of open water, the wind worked out in `ENTER_COST`, its
own widget (the wind) and its own counter symbol and picture; and
`farsuns` for production, units made in play, a map dealt out by
`SETUP`, its own orders, a side that never moves, and its own computer
player; and `tours` for a unit type of its own (spearmen who cancel the
cavalry's shock), `ON_ELIMINATE` (a leader's death), and a VP bonus
kept in `engine.bonus` (the plunder); and `severn` for a side that
gives up when it has lost half its steps (`engine.finish` from
`ON_TURN`), a ship that supports from the water, and a movement class
of its own for moving through woods; and `heights` for units that can't
fight and must get away (`EXITS` with `types`), a crossing closed until
a given turn (`ENTER_COST`), and night; and `roundtop` for a
one-time rule kept in `engine.flags` (the 20th Maine's charge: made
ready in `ON_TURN`, used in `COMBAT_SHIFTS`, spent once the unit has
attacked) and terrain of its own (the crest, Big Round Top, Plum Run);
and `maida` for a river worked out in code from the row where its south
bank begins, and both sides able to break (`engine.finish`); and
`carrhae` for horse archers made as a support type that runs out of
arrows (`CAN_SUPPORT`, with the quivers in `engine.flags`), a march
slowed under fire (`ENTER_COST`), its own sounds of battle, and the
stock computer player taught to ride back to the camels (`AI_CLASS`);
and `sanjuan` for a river that can be crossed only at fords (one of
them closed until a given turn, in `ENTER_COST`), a leader as a
counter of his own who helps the attacks he joins, and losses dealt
out at the start of a turn (`engine.take_losses` from `ON_TURN`); and
`rorkes` for a barricade and an inner wall worked out in code from the
hexes they enclose, ammunition that runs out (in `engine.flags`), a
building set on fire, a unit carried out of it by `ON_TURN`, and
the stock computer player taught to keep out of the flames (`AI_CLASS`);
and `pegasus` for a canal and a river that can be crossed only on
their bridges (hexsides of their own with no cost but along a road),
night, and a bonus for crossing a bridge (`ON_MOVE`); and `drvar` for
a leader who must escape off the map (`EXITS` with `types`) and whose
death ends the game (`ON_ELIMINATE` and `ON_TURN`), turns of different
lengths (`TURN_NAME`), and weather that supplies one side from the air;
and `fulda` for helicopters (a support type with a movement class of
its own that flies over everything, grounded at night by
`CAN_SUPPORT`), a sound of its own added to `sound.EFFECTS`, exits
from only part of an edge, and a game ended by `ON_END_TURN`; and
`hastings` for units that leave the line by themselves (moved and
disabled from `ON_TURN`, after the Norman steps were counted in
`engine.flags`), an objective with its own `shift` and `stand`, and
victory decided by an objective and a leader rather than points; and
`agincourt` for a hexside of its own (stakes, which horses pay more to
cross and attack across worse), a game built on `DEFENSIVE_FIRE`,
`STEP_VP` that differs by side, and a computer player that keeps its
line (`AI_CLASS`); and `cowpens` for support units that fire a set
number of volleys and must fall back to a leader to load again, and
postures that change on a given turn; and `tanga` for hidden things
dealt out by `SETUP` (the hives) and set off by `ON_MOVE`, a sound of
its own, popups, and a ship supporting from the harbour; and
`nagashino` for guns that must reload (a turn's firing recorded in
`ON_TURN`, checked in `CAN_SUPPORT`), units that never move (`m=0`),
and hexsides worked out in code along a column; and `belleau` for
losses taken while moving (`ON_MOVE` and `engine.take_losses`) and
units held until a given turn for an evening attack.

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
  `treasury`, `unit`, `orders`, `log`), and `CHROME`, their colours. A game can add
  widgets of its own with `@grognard.widget('name')`, terrain patterns
  with `@grognard.pattern('name')` and NATO symbols with
  `@grognard.symbol('name')`.
- `COMBAT_SOUND`: the sound of a fight when no unit has its own
  (`'gun'` by default; `'swords'` for blades). A unit or type's `fight`
  is its own (`'bow'` for archers); a barrage booms.
- `STYLE = 'pictures'` for little pictures on the counters instead of
  NATO symbols; `ZOOM` for the zoom a game starts at; `FONT` for the
  smooth text's font.
- `REACH = colour` tints the hexes a selected unit can reach, for a
  map too dark for the usual darkening of the rest to show (Far Suns).
- A terrain's `glyph`, `fn(surface, cx, cy, scale, hex)`, draws a
  picture in the middle of each of its hexes (Far Suns' suns), and
  `DRAW_MAP(game, surface)` draws over the map every frame (what a side
  knows of each star). A unit type's `values(unit)` says what its
  counter's numbers are (a world's people), and `under: True` puts it
  beneath the other units in its hex, and last to take losses.
- `AI_CLASS`: a computer player of the game's own, a subclass of
  `grognard.ai.AI`, for a game the stock one can't play. Besides moves
  and attacks its `next_action()` may return `('build', kind, hex)` and
  `('act', unit id, key)`.

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
