import pygame

from effects import load_enemy_art


class YellowEnemy:
    def __init__(self, position):
        self.position = pygame.Vector2(position)
        self.previous_position = self.position.copy()
        self.kind = "yellow_enemy"
        # Enemies share their pictures, but keep their own animation timers.
        self.frames, self.flash_frames = load_enemy_art("yellow_enemy")
        self.animation_time = 0
        self.hit_timer = 0
        self.health = 2
        self.max_health = 2
        self.score = 100
        self.radius = 26
        self.name = "Yellow Lv1"
        self.color = (255, 210, 65)
        self.bonus = False
        self.escaped = False
        self.warning = False

        # Three straight dashes, with a visible warning before each one.
        self.charge_cooldown = 0.6
        self.warning_timer = 0
        self.dash_timer = 0
        self.dashes_left = 0
        self.dash_direction = pygame.Vector2(0, 1)

    def update(self, dt, player, bullets):
        if dt <= 0:
            return

        if self.dash_timer > 0:
            dash_time = min(dt, self.dash_timer)
            self.position += self.dash_direction * 850 * dash_time
            self.dash_timer = max(0, self.dash_timer - dt)
            if self.dash_timer == 0:
                if self.dashes_left > 0:
                    self.start_warning(player, 0.32)
                else:
                    self.charge_cooldown = 1.2
            # Keep leftover frame time when a dash ends between frames.
            if dt > dash_time:
                self.update(dt - dash_time, player, bullets)
            return

        if self.warning_timer > 0:
            warning_time = min(dt, self.warning_timer)
            self.warning_timer = max(0, self.warning_timer - warning_time)
            if self.warning_timer == 0:
                self.warning = False
                self.dash_timer = 0.32
                self.dashes_left -= 1
            if dt > warning_time:
                self.update(dt - warning_time, player, bullets)
            return

        old_cooldown = self.charge_cooldown
        self.charge_cooldown = max(0, self.charge_cooldown - dt)
        to_player = player.position - self.position
        distance = to_player.length()
        if distance == 0:
            return

        direction = to_player / distance
        if distance < 700 and self.charge_cooldown == 0:
            # Chase during the last part of the cooldown, then warn.
            self.position += direction * 250 * min(dt, old_cooldown)
            self.dashes_left = 3
            self.start_warning(player, 0.5)
            if dt > old_cooldown:
                self.update(dt - old_cooldown, player, bullets)
        else:
            self.position += direction * 250 * dt

    def start_warning(self, player, duration):
        # Aim slightly ahead, then hold that direction so the dash is dodgeable.
        aim = player.position + player.velocity * 0.18 - self.position
        if aim.length_squared() > 0:
            self.dash_direction = aim.normalize()
        self.warning_timer = duration
        self.warning = True
