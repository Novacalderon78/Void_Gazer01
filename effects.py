import math
import random

import pygame

import config


# The final frame is empty, so each explosion fades away before it is removed.
DEATH_TIMES = (0.08, 0.07, 0.08, 0.09, 0.10, 0.12, 0.14, 0.22)
ENEMY_KINDS = ("yellow_enemy", "green_enemy", "red_enemy", "ufo")
enemy_art = {}
death_art = {}


def load_strip(path):
    strip = pygame.image.load(str(path)).convert_alpha()
    frames = []
    size = config.FRAME_SIZE
    for number in range(config.FRAME_COUNT):
        frame = strip.subsurface((number * size, 0, size, size)).copy()
        frames.append(frame)
    return frames


def load_enemy_art(name):
    # All enemies of the same type share these images, including hit flashes.
    if name not in enemy_art:
        path = config.GAME_FOLDER / "game_sprites/game_sprite_movement/strips"
        frames = load_strip(path / (name + "_strip.png"))
        flash_frames = []
        for frame in frames:
            flash = frame.copy()
            flash.fill((130, 130, 130, 0), special_flags=pygame.BLEND_RGBA_ADD)
            flash_frames.append(flash)
        enemy_art[name] = (frames, flash_frames)
    return enemy_art[name]


def load_death_frames(name):
    if name not in death_art:
        path = config.GAME_FOLDER / "game_sprites/game_enemy_death_effects/strips"
        death_art[name] = load_strip(path / (name + "_death_strip.png"))
    return death_art[name]


def preload():
    # Load once before playing so a new enemy never causes a disk-loading pause.
    for name in ENEMY_KINDS:
        load_enemy_art(name)
        load_death_frames(name)


class Explosion:
    def __init__(self, position, kind, color, score=0):
        self.position = pygame.Vector2(position)
        self.kind = kind
        self.color = color
        self.score = score
        self.time = 0
        self.duration = 0.9
        self.finished = False
        self.frame_index = 0
        self.score_image = None
        self.frame_times = DEATH_TIMES
        if kind == "boss":
            from boss import load_death_frames as load_boss_death, DEATH_FRAME_TIME
            self.frames = load_boss_death()
            self.frame_times = (DEATH_FRAME_TIME,) * len(self.frames)
            self.duration = sum(self.frame_times)
        else:
            self.frames = [] if kind == "player" else load_death_frames(kind)

        # The player has a larger burst, with sparks made from simple lines.
        self.sparks = []
        if kind in ("player", "boss"):
            count = 48 if kind == "boss" else 24
            for number in range(count):
                angle = number * math.tau / count + random.uniform(-0.08, 0.08)
                direction = pygame.Vector2(math.cos(angle), math.sin(angle))
                speed = random.uniform(75, 165) * (1.8 if kind == "boss" else 1)
                self.sparks.append((direction, speed))

    def update(self, dt):
        self.time = min(self.duration, self.time + max(0, dt))
        self.finished = self.time >= self.duration - 0.000001

        # Use the strip's timing once, without looping back to the ship.
        frame_end = 0
        self.frame_index = len(self.frame_times) - 1
        for number, frame_time in enumerate(self.frame_times):
            frame_end += frame_time
            if self.time < frame_end:
                self.frame_index = number
                break

    def draw(self, screen, player_position, font):
        if self.finished:
            return
        center = pygame.Vector2(screen.get_rect().center)
        point = self.position - player_position + center

        # Skip drawing effects far outside the view. Their timers still finish.
        if not screen.get_rect().inflate(400, 400).collidepoint(point):
            return

        if self.kind == "player":
            self.draw_player_burst(screen, point)
        else:
            image = self.frames[self.frame_index]
            screen.blit(image, image.get_rect(center=(round(point.x), round(point.y))))
            if self.kind == "boss":
                self.draw_player_burst(screen, point)

        if self.score > 0 and font is not None:
            if self.score_image is None:
                self.score_image = font.render("+" + str(self.score), True, self.color)
            popup = (round(point.x), round(point.y - 52 - self.time * 45))
            screen.blit(self.score_image, self.score_image.get_rect(center=popup))

    def draw_player_burst(self, screen, point):
        progress = self.time / self.duration
        brightness = (1 - progress) ** 1.5
        orange = tuple(round(value * brightness) for value in (255, 130, 45))
        gold = tuple(round(value * brightness) for value in (255, 225, 135))
        center = (round(point.x), round(point.y))

        # Two expanding rings and a brief bright core make the impact readable.
        radius = round(8 + progress * (230 if self.kind == "boss" else 130))
        pygame.draw.circle(screen, orange, center, radius, max(1, round(5 * (1 - progress))))
        if progress < 0.5:
            pygame.draw.circle(screen, gold, center, max(1, round(30 * (1 - progress * 2))))
            pygame.draw.circle(screen, orange, center, max(1, radius // 2), 2)

        for direction, speed in self.sparks:
            distance = speed * self.time * (1 - progress * 0.3)
            head = point + direction * distance
            tail = head - direction * (4 + 15 * (1 - progress))
            pygame.draw.line(screen, orange, tail, head, 3)
            pygame.draw.line(screen, gold, tail, head, 1)
