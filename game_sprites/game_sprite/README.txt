GAME SPRITES

Five transparent RGBA PNG sprites extracted from the supplied 800 x 600 single-frame GIF.
The source pixels are not resized, smoothed, or redrawn. Foreground RGB colors are retained.
Exterior background, stars, and near-background edge noise are removed.

FILES
sprites/ : individual sprites, tightly cropped
sprite_sheet.png : 640 x 128 transparent sheet; five 128 x 128 cells
sprites.json : sprite rectangles, tile rectangles, and source coordinates

SHEET ORDER (left to right)
1. ufo: 65 x 33 px
2. red_enemy: 71 x 48 px
3. green_enemy: 40 x 47 px
4. yellow_enemy: 43 x 66 px
5. player_spaceship: 96 x 112 px

Sprites are centered in their cells at original scale. Sheet has no labels or background.
Use nearest-neighbor filtering and integer scale factors when enlarging in a game engine.
This is a static set: the uploaded GIF contains one frame.
