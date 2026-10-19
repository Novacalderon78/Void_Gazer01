# Void Gazer

Double-click `run_game.bat` to play.

To test just the boss, open the `boss_test` folder and double-click:

- `full_health.bat` starts the boss with all 320 health.
- `one_health.bat` starts it with 1 health, so one shot tests its death sequence.

Both tests skip straight to the boss entrance with your ship at full health.
WASD and mouse controls work normally. Play Again repeats the selected test.

The main game files are:

- `main.py` opens the window and runs the game loop.
- `player.py` moves, rotates, animates, and shoots lasers from the spaceship.
- `config.py` contains settings such as window size and ship speed.
- `effects.py` loads shared animation frames and plays explosions.
- `menu.py` draws the start menu and final-score screen.
- `items.py` creates and collects random item drops.
- `boss.py` animates the boss and controls its three attack phases.
- `arena.py` draws the boss arena and applies its outside-area warning and damage.
- `projectiles.py` moves and draws enemy shots, mines, meteors, laser columns, and returning blades.
- `sounds.py` loads death and boss sounds and creates the nitro and laser alarm sounds.
- `warning.py` draws boss danger zones, countdowns, and health alerts.

Each enemy has its own file, health, score, and ability:

| Enemy file | Difficulty | Hits to defeat | Points | Ability |
| --- | --- | --- | --- | --- |
| `yellow_enemy.py` | Level 1 | 2 | 100 | Pursues at 250 pixels per second, then makes three predictive charges at 850, with a separate warning before each. |
| `green_enemy.py` | Level 3 | 3 | 300 | Orbits faster and fires four predictive shots at 450 pixels per second. Its last shot adds two angled flank shots. |
| `red_enemy.py` | Level 5 | 5 | 600 | Strafes across your aim and fires three warned spreads of seven, five, and three shots, each faster than the last. |
| `ufo.py` | Bonus | 2 | 1,000 | Crosses at 335 pixels per second, boosts to 520, dodges lasers within 220 pixels, and escapes after 8 seconds. |

These levels describe enemy difficulty. All four types can appear from the
start. Shoot enemies to earn points; UFOs only award points when destroyed.
The bonus UFO does not attack you.
Each round starts easier: hostile enemies move and attack at 65% pace, with
one new enemy every 3 seconds and at most 8 enemies at once.

Every 5,000 points increases difficulty: 5,000, 10,000, 15,000, and so on.
Existing and new hostiles move and attack faster, spawn delays shorten, and
the enemy limit increases by 4 each level, up to 40. Waves also grow from
1 enemy to 2, 3, 4, 5, then 6 enemies at a time. They only fill available
spaces, so the limit is never exceeded. The HUD shows the current enemy count,
limit, and next milestone. Normal enemy health does not increase. Attack
speed and spawning have gentle limits to keep the game manageable. Peaceful
UFOs keep their normal movement and 8-second escape timer.

A new round resets difficulty, regardless of your session best score. Attack
warnings remain visible, and bullets expire instead of building up forever.

The final **Void Reaver** boss arrives at **10,000 points**. Normal enemies,
their bullets, and leftover pickups clear away for a solo fight. A roar and a two-second warning
come before the boss descends from above. It lands with a growl, shockwave,
sparks, flash, and brief screen shake. The warning and entrance are protected,
so you can get ready before combat starts.

The boss sounds are in `SFX/BossSFX`:

- `roar-329857.mp3` warns you before the boss appears.
- `growl-390285.mp3` plays once when the boss lands on screen.
- `growl-376892.mp3` plays occasionally during combat, 6–10 seconds apart.
- `monster-scream-aggressive.mp3` plays once when the boss dies.

Boss sounds pause with the game. Starting a new round, returning to the menu,
or losing your ship stops them. Missing sounds do not prevent the game running.
The boss uses your existing alien artwork, including its firing and death
animations. Its large health bar shows the three phases:

- **Phase 1 — Hunter:** cycles through Homing Fan, Void Ring, Rift Ambush,
  three charges, Reaper Blades, and Starfall.
- **Phase 2 — Exposed Core:** begins at two-thirds health. Its sequence is
  Spiral, Crossfire, Ion Storm, Reaper Blades, Deathray, Rift Ambush, Void Mines,
  Starfall, four charges, Void Ring, and Homing Fan.
- **Phase 3 — Final Fury:** begins at one-third health. Its sequence is
  Deathray, Crossfire, Rift Ambush, Reaper Blades, five charges, Ion Storm, Starfall,
  Void Mines, Spiral, Void Ring, and Homing Fan. Bursts grow larger and attack breaks
  become shorter.

The boss chooses from these attacks without immediately repeating the same one.
It watches sustained circling and straight-line escape, then favors attacks
that challenge that movement. Every phase's attack bag contains all its attacks.

These eleven attacks have visible warnings. Homing Fan fires 12, 14, or 16
shots as phases advance. They track you for 1.1 seconds in phase 1 and 1.3
seconds in later phases, then fly straight; change direction to avoid them.
Ring volleys leave a marked escape gap. Charge warnings outline the boss's
full path. Spiral sends three rotating streams outward in phase 2 and four
in phase 3. Mines mark their positions before appearing, then fill a circular
timer before bursting into flying shards. The mine markers themselves do not
damage your ship.

Crossfire opens two fixed, marked portals on opposite sides of you. After a
0.8-second warning, they fire five paired volleys over 1.4 seconds, aimed ahead
of your movement.
Watch their lines and move between the spreads. Starfall marks falling meteor
paths for 0.85 seconds, then drops six meteors, or eight in the final phase.
Each meteor splits into six flying shards after another 0.85 seconds.

Reaper Blades shows a 0.9-second warning with outward paths, turning points,
and return arrows. It releases six, eight, or ten spinning blades as phases
advance. They fly outward at 460 pixels per second for 0.65 seconds, then
return at 520 to the boss's fixed launch position and disappear. Moving away
from the first pass can put you in a returning blade's path, so watch both legs.

Ion Storm marks three vertical purple columns, or five in the final phase.
You have 1.05 seconds to move between the marked lanes before they fire for
0.45 seconds. Rift Ambush shows a fixed landing zone and a ghost of the boss
for 1.05 seconds. Leave that circle before the boss lands and releases an orb
wave. Green edges mark its 90-degree escape gap. The teleport path cannot
damage you; the marked landing zone is the danger.

The Deathray appears in phases 2 and 3. Its 1.65-second warning briefly tracks
your movement, then locks its sweep direction. A shaded red half-circle marks
the full danger area, with bold borders, green edges, a countdown, and an arrow
showing the sweep direction. Move behind the boss, beyond the green edges,
before it fires. Hold Space for nitro if you need more speed. Nitro does not
protect you from the laser.

Warning beeps grow faster near firing, followed by a firing cue. The beam makes
a 180-degree sweep over 2.3 seconds. Its range is at least 5,000 pixels and
extends if you fly farther away. Flying away or reducing the boss below a phase
threshold does not cancel its warning or active sweep. The ray finishes before
the next phase starts; defeating the boss still stops it immediately.

Each repeated burst or charge has its own warning. Boss warnings always use
real seconds, even on higher difficulty. If you fly too far away, the boss
rushes back into range between attacks. An arrow at the edge of the screen
points toward the boss when it moves offscreen and warns when its Deathray
is charging or firing. Blue edge arrows show offscreen Crossfire portals.
Red edge glows and large attack warnings keep the ship visible in the middle
of the screen. Mild screen shake adds impact while the HUD and aiming stay
steady. The HUD also warns when your hull is critical or the boss is enraged.

Support blasts overlap the main attacks. Orange circles mark predicted positions
for 0.85 seconds before a 0.35-second blast with a 72-pixel radius. Each phase
adds 2, 3, or 4 marked spots every 2.7, 2.1, or 1.6 seconds, leaving sampled
escape routes. Change direction when a marker appears under your route.

The boss arena locks when combat starts. Its radius shrinks gradually from 720
to 660 and then 600 pixels. Staying outside for 0.85 seconds starts storm damage;
return inside the segmented ring. Phase changes and Rift warnings give a
protected break. The arena does not teleport you or change your fuel or speed.

Each new phase clears old enemy shots and mines and gives you a short protected
pause while the boss changes color. Normal recovery breaks shorten from 0.5
seconds in phase 1 to 0.35 in phase 2 and 0.25 in phase 3. At 15% health, the
boss becomes enraged and shortens these breaks further. Keep moving and watch
its attack name.
Boss projectiles are limited to 240 at once and disappear after a short time.
The boss has 320 health. Defeating it awards **5,000 points** and finishes the
game. Combat stops immediately while its death animation and scream play.
Then the victory screen shows your final score, session best, and completion
time. No enemies or bosses spawn after you win. Click Play Again or press
Enter for a fresh game; click Main Menu or press M to return to the start.

You start with 5 health. Enemy shots and normal enemy collisions cost 1 health.
Touching the boss or being hit by its Deathray costs 2 health. After a hit,
your ship blinks and has one second of protection.
Your health bar appears in the HUD and below your ship, changing from green
to yellow to red as health falls. Healing pickups refill it.

The game opens at a start menu showing every enemy and its points. Click Start
or press Enter to play. After your ship explodes, the final-score screen shows
your score, best score, and survival time. Click Play Again or press Enter for
a new round; click Main Menu or press M to return to the start menu.
Defeat the boss to reach the victory screen instead.

Enemies have a 35% chance to drop one random item when destroyed:

- **Health:** restores 1 health. It stays on the ground if you are already at full health.
- **Rapid fire:** doubles your firing rate for 6 seconds.
- **Bonus points:** adds 250 points to your score.

Move over an item to collect it before it disappears after 15 seconds. Item
timers and rapid fire freeze while paused. A new round clears all old items
and temporary upgrades.

Enemy movement and death animations use the existing sprite strips. Death
animations play once, then disappear. Your ship also explodes before the game
over screen appears. Enemies flash when hit, and the UFO label shows how much
time remains before it escapes.

Destroyed yellow, green, red, and UFO enemies play `SFX/enemySFX/lasgun.mp3`
once when defeated. Sounds pause with the game and stop on a new round,
player death, or victory. Two clips can overlap without interrupting boss audio.

When your health reaches zero, `SFX/plyerSFX/plyerdie.mp3` plays once with your
ship's explosion. It continues into the final-score screen, pauses when the
window loses focus, and stops when you start again, return to the menu, or quit.

The crosshair follows the mouse and shows when the laser is ready. Your best
score stays visible between restarts while the game window is open.

Your original pictures are in `game_sprites`, and sounds are in `SFX`.

Controls: **WASD** move, **mouse** aim, **left click** shoot, **hold Space** nitro,
**P** pause, **Esc** exit. There is no reset key during play.

W moves up, S down, A left, and D right, independently of where you aim.
The ship faces the mouse, so you can circle enemies and shoot while moving
sideways or backward. Diagonal movement has the same speed as moving straight.
Movement starts quickly and stops shortly after you release the keys.

Hold **Space** to use nitro at 820 pixels per second, compared with the normal
400. Steer continuously with WASD while boosting. If no movement keys are held,
nitro follows your mouse aim. Fuel is capped at **100**, displayed as **100%**.
It drains 40 fuel per second, giving you **2.5 seconds** of boost from a full tank.

Release Space to stop boosting. After a 0.75-second delay, fuel returns at
25 per second. If the tank runs empty, it locks until you have at least 20 fuel
and release Space. Holding Space after exhaustion does not restart the boost.
Fuel refills to 100. The HUD shows recharge progress and a **RELEASE SPACE**
hint when ready after an empty tank.
Orange and blue exhaust streaks and an engine sound show when nitro is active.
Nitro gives extra speed without damage protection; bullets and boss attacks
can still hurt you. Pause freezes fuel use, recharge, and the engine sound.

The warning beeps, firing cue, and nitro engine sound are generated in
`sounds.py`, so they need no extra audio files.

Lasers fire toward the mouse cursor. Hold the left mouse button to keep firing.
Each shot travels straight after firing; moving the cursor aims the next shot.
The laser sound is in `SFX/fox-laser-gun.mp3`.

Artwork, hit flashes, and unchanged text are loaded or drawn once and reused.
Old shots and finished explosions are removed automatically. The game also
reduces its frame rate while paused to save processing time.

To set up another computer, install Python 3.12, open a terminal in this folder,
and run:

```powershell
python -m pip install pygame
python -B main.py
```
