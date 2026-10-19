import random

import pygame

from effects import load_enemy_art


class GreenEnemy:
    def __init__(self, position):
        self.position = pygame.Vector2(position)
        self.previous_position = self.position.copy()
        self.kind = "green_enemy"
        # Enemies share their pictures, but keep their own animation timers.
        self.frames, self.flash_frames = load_enemy_art("green_enemy")
        self.animation_time = 0
        self.hit_timer = 0
        self.health = 3
        self.max_health = 3
        self.score = 300
        self.radius = 23
        self.name = "Green Lv3"
        self.color = (105, 235, 120)
        self.bonus = False
        self.escaped = False
        self.warning = False

        # A warning ring appears before each four-shot burst.
        self.shoot_timer = 0.55
        self.burst_left = 0
        self.orbit_direction = random.choice([-1, 1])
        self.orbit_timer = 2.5

    def update(self, dt, player, bullets):
        if dt <= 0:
            return

        to_player = player.position - self.position
        distance = to_player.length()
        direction = pygame.Vector2(0, 1)
        if distance > 0:
            direction = to_player / distance

        # Reverse the orbit every few seconds to zigzag around the player.
        self.orbit_timer -= dt
        if self.orbit_timer <= 0:
            turns = int(-self.orbit_timer / 2.5) + 1
            if turns % 2:
                self.orbit_direction *= -1
            self.orbit_timer += turns * 2.5

        # Circle at 280 pixels, and close the gap quickly if the player flees.
        sideways = pygame.Vector2(-direction.y, direction.x)
        sideways *= self.orbit_direction
        approach_speed = max(-180, min(240, (distance - 280) * 1.1))
        self.position += (sideways * 210 + direction * approach_speed) * dt

        self.shoot_timer -= dt
        shots_fired = 0
        while self.shoot_timer <= 0:
            if self.burst_left == 0:
                # The ring lights up before the first shot of every burst.
                self.warning = True
                self.burst_left = 4
                self.shoot_timer += 0.3
                continue

            self.warning = False
            aim = player.position - self.position
            lead_time = min(0.35, aim.length() / 450)
            lead = player.velocity * lead_time
            if lead.length_squared() > 180 * 180:
                lead.scale_to_length(180)
            aim += lead
            if aim.length_squared() > 0:
                aim = aim.normalize()
            else:
                aim = direction
            # The last shot splits sideways to catch a simple circular escape.
            angles = (0, -22, 22) if self.burst_left == 1 else (0,)
            for angle in angles:
                shot_direction = aim.rotate(angle)
                bullets.append({
                    "position": self.position + shot_direction * (self.radius + 10),
                    "velocity": shot_direction * 450,
                    "time_left": 3.0,
                    "color": self.color,
                    "damage": 1,
                })
            self.burst_left -= 1
            self.shoot_timer += 0.13 if self.burst_left else 1.05
            shots_fired += 1
            # A stalled frame cannot create more than one full burst at once.
            if shots_fired == 4:
                self.shoot_timer = max(0, self.shoot_timer)
                break
