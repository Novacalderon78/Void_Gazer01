GAME SPRITES - ENEMY DEATH EFFECTS

These are newly created pixel-art enemy death effects based on the supplied static sprites.
They were created with the built-in image_gen tool, not recovered from the original screenshot.
The original static sprite and movement packages remain separate and unchanged.

CONTENTS
frames/<type>/ : 8 separate transparent RGBA PNG frames per enemy, 128 x 128 px
strips/ : 4 transparent 1024 x 128 horizontal strips
animations/ : 4 transparent animated PNGs (.png/APNG), total play count ONE
previews/ : repeating GIF previews with a blank end pause on a dark checkerboard
generated_atlases/ : unmodified generated 4 x 2 originals at full detail
death_sprite_sheet.png : transparent 1024 x 512 sprite sheet
death_preview.gif : animated overview of all four enemy types
death_preview.png : still preview
death_effects.json : frame rectangles, durations, pivots, stages, source transforms, and QA
death_effect_prompt_notes.txt : creation method and prompt notes (when supplied)

SHEET LAYOUT
Rows top to bottom: UFO, red enemy, green enemy, yellow enemy.
Columns left to right: frames 00 through 07.
Each cell: 128 x 128 px; common pivot: (64, 64).
Stages: hit flash, breakup, fire burst, expansion, fading debris, dissipation, last sparks, transparent end.
Frame durations in ms: 80, 70, 80, 90, 100, 120, 140, 220
Total playback duration: 900 ms

USE IN YOUR GAME
When an enemy dies, replace it with this effect and play frames 00 to 07 ONCE.
After frame 07, remove the effect. Do not enable looping in your game engine.
Frame 07 is genuinely transparent, giving a clean finish with no surviving enemy.
Use nearest-neighbor filtering to preserve the pixel edges.
One common crop, scale, and offset is used across all frames of each enemy.
Expanding particles retain their relative positions and fit inside 112 x 112 px.
Original generated atlases are retained unmodified. If configured, the last packaged cell is explicitly blanked; metadata records this.
The tiny configured alpha floor removes near-invisible exterior noise only; other alpha is retained.
APNGs play once and stay transparent at the end. GIF previews repeat only for convenient viewing.
GIF preview timing matches the effects except that the final blank is held for 650 ms.
The checkerboard appears only in previews; game asset PNGs are transparent.

The ZIP includes all files in this package except itself.
