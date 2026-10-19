import math
import random
import pygame
from effects import load_enemy_art


class UFO:
    def __init__(self, position):
        self.position = pygame.Vector2(position)
        self.previous_position = self.position.copy()
        self.kind = "ufo"
        # Enemies share their pictures, but keep their own animation timers.
        self.frames, self.flash_frames = load_enemy_art("ufo")
        self.animation_time = 0
        self.hit_timer = 0
        self.name = "UFO Bonus"
        self.color = (190, 140, 255)
        self.health = 2
        self.max_health = 2
        self.score = 1000
        self.radius = 30
        self.bonus = True
        self.escaped = False
        self.warning = False
        self.time_left = 8.0
        self.elapsed = 0
        self.weave_phase = random.uniform(0, math.tau)
        self.direction = None
        self.boost_timer = 1.8
        self.boost_time_left = 0
        self.dodge_cooldown = 0
        self.dodge_direction = pygame.Vector2()

    def update(self, dt, player, bullets):
        if dt <= 0 or self.escaped:
            return

        # Pick one crossing direction, then keep going until it escapes.
        if self.direction is None:
            difference = player.position - self.position
            if difference.length_squared() > 0:
                self.direction = difference.normalize()
            else:
                self.direction = pygame.Vector2(1, 0)

        self.elapsed += dt
        sideways = self.direction.rotate(90)
        weave = math.sin(self.elapsed * 4 + self.weave_phase) * 140
        self.boost_timer -= dt
        self.boost_time_left = max(0, self.boost_time_left - dt)
        self.dodge_cooldown = max(0, self.dodge_cooldown - dt)
        if self.boost_time_left == 0:
            self.dodge_direction.update(0, 0)

        # Brief bursts make the bonus ship harder to catch.
        if self.boost_timer <= 0:
            self.boost_time_left = 0.4
            self.boost_timer = 1.8

        # Dodge sideways away from the closest nearby player laser.
        if self.dodge_cooldown == 0:
            closest_laser = None
            closest_distance = 220 * 220
            for laser in player.lasers:
                difference = laser["position"] - self.position
                distance = difference.length_squared()
                if distance < closest_distance:
                    closest_laser = laser
                    closest_distance = distance
            if closest_laser is not None:
                difference = closest_laser["position"] - self.position
                if difference.dot(sideways) >= 0:
                    self.dodge_direction = -sideways
                else:
                    self.dodge_direction = sideways
                self.boost_time_left = 0.4
                self.dodge_cooldown = 0.8

        velocity = self.direction * 335 + sideways * weave
        if self.boost_time_left > 0:
            velocity += self.dodge_direction * 300
            velocity.scale_to_length(520)
        self.position += velocity * dt

        # The bonus UFO never shoots. Catch it before its timer runs out.
        self.time_left = max(0, self.time_left - dt)
        if self.time_left <= 0:
            self.escaped = True
