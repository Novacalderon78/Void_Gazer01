# Change these values to adjust the game.

from pathlib import Path

TITLE = "Void Gazer"
WIDTH = 1280
HEIGHT = 800
FPS = 60

BACKGROUND_COLOR = (5, 9, 19)
TEXT_COLOR = (220, 235, 245)
STAR_COUNT = 180

# WASD moves across the screen. Releasing the keys quickly stops the ship.
PLAYER_MAX_SPEED = 400
PLAYER_ACCELERATION = 3000
PLAYER_STOP_SPEED = 4200
PLAYER_HEALTH = 5
PLAYER_HIT_RADIUS = 32
PLAYER_HIT_COOLDOWN = 1.0
PLAYER_NITRO_SPEED = 820
# Full tank: 2.5 seconds of continuous boost.
PLAYER_NITRO_FUEL = 100
PLAYER_NITRO_DRAIN = 40
PLAYER_NITRO_RECHARGE = 25
PLAYER_NITRO_RECHARGE_DELAY = 0.75
PLAYER_NITRO_RESTART_FUEL = 20

# Start gently, then increase pressure every 5,000 points.
DIFFICULTY_SCORE_STEP = 5000
ENEMY_START_PACE = 0.65
ENEMY_TOP_PACE = 1.5
ENEMY_SPAWN_TIME = 3.0
MIN_ENEMY_SPAWN_TIME = 1.0
BASE_ENEMY_LIMIT = 8
ENEMIES_PER_LEVEL = 4
MAX_ENEMIES = 40
MAX_SPAWN_AMOUNT = 6
MAX_ENEMY_BULLETS = 400
DESPAWN_DISTANCE = 2400
MAX_EXPLOSIONS = 24

# Defeat the final boss at 10,000 points to finish the game.
BOSS_SCORE_TARGET = 10000
BOSS_HEALTH = 320
BOSS_SCORE = 5000
BOSS_BULLET_LIMIT = 240
# The beam extends further if the player flies beyond this distance.
BOSS_LASER_RANGE = 5000
BOSS_LASER_DAMAGE = 2
BOSS_CONTACT_DAMAGE = 2
# Landing distance above the player leaves room below the boss health bar.
BOSS_ENTRY_DISTANCE = 190

# Enemies sometimes leave a pickup when destroyed.
ITEM_DROP_CHANCE = 0.35
MAX_ITEMS = 12
ITEM_LIFETIME = 15.0
ITEM_PICKUP_RADIUS = 50
ITEM_BONUS_POINTS = 250
RAPID_FIRE_DURATION = 6.0

# Laser settings.
LASER_SPEED = 900
LASER_COOLDOWN = 0.18  # Seconds between shots while holding the left mouse button.
LASER_LIFETIME = 1.4
LASER_LENGTH = 24
LASER_COLOR = (60, 220, 255)

# Normal ship animation frames are 128 x 128 pixels.
FRAME_SIZE = 128
FRAME_COUNT = 8
FRAME_TIME = 0.1

GAME_FOLDER = Path(__file__).resolve().parent
PLAYER_IMAGE = GAME_FOLDER / "game_sprites/game_sprite/sprites/player_spaceship.png"
PLAYER_ANIMATION = GAME_FOLDER / "game_sprites/game_sprite_movement/strips/player_spaceship_strip.png"
LASER_SOUND = GAME_FOLDER / "SFX/fox-laser-gun.mp3"
PLAYER_DEATH_SOUND = GAME_FOLDER / "SFX/plyerSFX/plyerdie.mp3"
ENEMY_DEATH_SOUNDS = (
    GAME_FOLDER / "SFX/enemySFX/lasgun.mp3",
)
BOSS_SOUNDS = {
    "roar": GAME_FOLDER / "SFX/BossSFX/roar-329857.mp3",
    "arrival": GAME_FOLDER / "SFX/BossSFX/growl-390285.mp3",
    "combat": GAME_FOLDER / "SFX/BossSFX/growl-376892.mp3",
    "death": GAME_FOLDER / "SFX/BossSFX/monster-scream-aggressive.mp3",
}
