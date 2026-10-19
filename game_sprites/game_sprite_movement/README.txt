GAME SPRITES - MOVEMENT

This is newly created movement animation based on the supplied single-frame screenshot.
The original 800 x 600 GIF contains one frame; these poses were generated, not recovered from the source.
The original static sprite package remains separate and unchanged.
Created with the built-in image_gen tool using the extracted static sprite images as references.

CONTENTS
frames/<type>/ : 8 separate transparent RGBA PNG frames per sprite, 128 x 128 px
strips/ : one transparent 1024 x 128 horizontal strip per sprite
animations/ : transparent animated PNG (.png / APNG), 8 frames, loops forever
previews/ : animated GIF previews on a fixed dark checker background
generated_atlases/ : unmodified original generated 4 x 2 atlases at full detail
movement_sprite_sheet.png : transparent 1024 x 640 sprite sheet
movement_preview.gif : animated overview of all five sprite types
movement_preview.png : still preview
movement.json : frame rectangles, timing, pivots, source atlas details, QA
animation_prompt_notes.txt : creation method and prompt notes

SHEET LAYOUT
Rows, top to bottom: ufo, red_enemy, green_enemy, yellow_enemy, player_spaceship
Columns, left to right: frames 00 to 07.
Each cell is 128 x 128 px. Pivot is (64,64).
Frame durations in ms: 100, 100, 100, 100, 100, 100, 100, 100
Loop duration: 800 ms

USE
Import PNG frames or strips into your game and play frames in order on a loop.
Use nearest-neighbor filtering. Do not smooth the pixels.
All frames of each sprite use one common crop, scale, and offset so their positions remain consistent.
When needed, original canvases receive transparent padding to form exact equal cells.
Near-invisible exterior alpha noise is removed only at each configured alpha floor; all other alpha is retained.
The dark checkerboard appears only in GIF/still previews; PNG assets retain transparency.

The ZIP includes every file in this movement package except the ZIP itself.
