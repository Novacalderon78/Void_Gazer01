import pygame
from effects import load_enemy_art


class RedEnemy:
    def __init__(self, position):
        self.position = pygame.Vector2(position)
        self.previous_position = self.position.copy()
        self.kind = "red_enemy"
        # Enemies share their pictures, but keep their own animation timers.
        self.frames, self.flash_frames = load_enemy_art("red_enemy")
        self.animation_time = 0
        self.hit_timer = 0
        self.name = "Red Lv5"
        self.color = (255, 90, 100)
        self.health = 5
        self.max_health = 5
        self.score = 600
        self.radius = 30
        self.bonus = False
        self.escaped = False
        self.warning = False
        self.shoot_timer = 1.2
        self.volley = 0
        self.strafe_direction = 1

    def update(self, dt, player, bullets):
        if dt <= 0:
            return

        difference = player.position - self.position
        distance = difference.length()
        direction = pygame.Vector2(0, -1)
        if distance > 0:
            direction = difference.normalize()

        # This armored enemy tries to stay at shooting distance.
        if distance > 380:
            self.position += direction * 200 * dt
        elif 0 < distance < 300:
            self.position -= direction * 150 * dt

        # Keep moving across the player's aim while preparing a volley.
        if distance < 650 and (self.volley > 0 or self.shoot_timer <= 0.5):
            sideways = pygame.Vector2(-direction.y, direction.x)
            self.position += sideways * self.strafe_direction * 100 * dt

        self.shoot_timer -= dt
        volleys_fired = 0
        while self.shoot_timer <= 0:
            # Aim slightly ahead of the ship, with a limit on the prediction.
            lead = player.velocity * 0.2
            if lead.length_squared() > 90 * 90:
                lead.scale_to_length(90)
            aim = player.position + lead - self.position
            if aim.length_squared() > 0:
                direction = aim.normalize()

            # Three staggered spreads close the gaps left by the previous shots.
            if self.volley == 0:
                angles = (-42, -28, -14, 0, 14, 28, 42)
                speed = 400
                self.volley = 1
                self.shoot_timer += 0.25
            elif self.volley == 1:
                angles = (-35, -17.5, 0, 17.5, 35)
                speed = 435
                self.volley = 2
                self.shoot_timer += 0.25
            else:
                angles = (-12, 0, 12)
                speed = 465
                self.volley = 0
                self.shoot_timer += 1.55
                self.strafe_direction *= -1

            for angle in angles:
                shot_direction = direction.rotate(angle)
                bullets.append({
                    "position": self.position + shot_direction * (self.radius + 10),
                    "velocity": shot_direction * speed,
                    "time_left": 3.0,
                    "color": self.color,
                    "damage": 1,
                })
            volleys_fired += 1
            # A stalled frame cannot release more than one whole combo.
            if volleys_fired == 3:
                self.shoot_timer = max(0, self.shoot_timer)
                break

        self.warning = self.volley > 0 or self.shoot_timer <= 0.5
