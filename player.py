import pygame
import config
from effects import load_strip


class Player:
    def __init__(self):
        # Put the idle ship on a canvas the same size as the animation frames.
        original = pygame.image.load(str(config.PLAYER_IMAGE)).convert_alpha()
        self.idle_image = pygame.Surface(
            (config.FRAME_SIZE, config.FRAME_SIZE), pygame.SRCALPHA
        )
        image_rect = original.get_rect(center=self.idle_image.get_rect().center)
        self.idle_image.blit(original, image_rect)

        self.frames = load_strip(config.PLAYER_ANIMATION)

        # Sound is optional if the computer has no working audio device.
        self.laser_sound = None
        if pygame.mixer.get_init():
            try:
                self.laser_sound = pygame.mixer.Sound(str(config.LASER_SOUND))
                self.laser_sound.set_volume(0.3)
            except (pygame.error, OSError):
                # Missing sounds or unsupported formats should not stop the game.
                self.laser_sound = None

        self.reset()

    def reset(self):
        self.position = pygame.Vector2(0, 0)
        self.previous_position = self.position.copy()
        self.velocity = pygame.Vector2(0, 0)
        self.angle = 0
        self.animation_time = 0
        self.thrusting = False
        self.lasers = []
        self.shoot_timer = 0
        self.rapid_fire_timer = 0
        self.health = config.PLAYER_HEALTH
        self.hit_timer = 0
        self.death_effect_played = False
        self.rotation_key = None
        self.rotated_image = None
        self.nitro_active = False
        self.nitro_fuel = float(config.PLAYER_NITRO_FUEL)
        self.nitro_locked = False
        self.nitro_recharge_timer = 0
        self.nitro_direction = pygame.Vector2(0, -1)
        self.nitro_trail = []

    def stop_nitro(self):
        # Finishing a round stops the engine without refilling its tank.
        self.nitro_active = False
        self.nitro_trail.clear()
        self.velocity.update(0, 0)
        self.thrusting = False

    def update(self, keys, dt, mouse_position=None, shooting=False):
        if dt <= 0:
            return
        self.previous_position = self.position.copy()
        if self.health <= 0:
            self.stop_nitro()
            return

        self.hit_timer = max(0, self.hit_timer - dt)
        self.rapid_fire_timer = max(0, self.rapid_fire_timer - dt)
        self.nitro_trail = [
            (position, direction, age + dt)
            for position, direction, age in self.nitro_trail
            if age + dt < 0.22
        ]

        # Face the mouse independently of the movement keys.
        aim = pygame.Vector2()
        if mouse_position is not None:
            center = pygame.Vector2(config.WIDTH // 2, config.HEIGHT // 2)
            aim = pygame.Vector2(mouse_position) - center
            if aim.length_squared() > 0:
                aim = aim.normalize()
                self.angle = pygame.Vector2(0, -1).angle_to(aim) % 360

        # WASD always moves up, down, left, and right on the screen.
        movement = pygame.Vector2()
        if keys[pygame.K_w]:
            movement.y -= 1
        if keys[pygame.K_s]:
            movement.y += 1
        if keys[pygame.K_a]:
            movement.x -= 1
        if keys[pygame.K_d]:
            movement.x += 1

        moving = movement.length_squared() > 0
        if moving:
            movement = movement.normalize()

        # Hold Space for nitro. WASD can steer it throughout the boost.
        try:
            nitro_pressed = bool(keys[pygame.K_SPACE])
        except (KeyError, IndexError):
            nitro_pressed = False
        if not nitro_pressed and self.nitro_fuel >= config.PLAYER_NITRO_RESTART_FUEL:
            self.nitro_locked = False

        self.nitro_active = False
        move_time = dt
        if nitro_pressed and not self.nitro_locked and self.nitro_fuel > 0:
            if moving:
                self.nitro_direction = movement.copy()
            elif aim.length_squared() > 0:
                self.nitro_direction = aim.copy()
            else:
                self.nitro_direction = pygame.Vector2(0, -1).rotate(self.angle)

            # An almost-empty tank only boosts for the time its fuel can cover.
            boost_time = min(dt, self.nitro_fuel / config.PLAYER_NITRO_DRAIN)
            self.velocity = self.nitro_direction * config.PLAYER_NITRO_SPEED
            self.position += self.velocity * boost_time
            self.nitro_fuel = max(0, self.nitro_fuel - config.PLAYER_NITRO_DRAIN * boost_time)
            if self.nitro_fuel < 0.000000001:
                self.nitro_fuel = 0
                self.nitro_locked = True
            else:
                self.nitro_active = True
            self.nitro_recharge_timer = config.PLAYER_NITRO_RECHARGE_DELAY
            self.nitro_trail.append(
                (self.previous_position.copy(), self.nitro_direction.copy(), 0)
            )
            self.nitro_trail = self.nitro_trail[-8:]
            move_time = max(0, dt - boost_time)

        if move_time > 0:
            recharge_time = max(0, move_time - self.nitro_recharge_timer)
            self.nitro_recharge_timer = max(0, self.nitro_recharge_timer - move_time)
            self.nitro_fuel = min(
                config.PLAYER_NITRO_FUEL,
                self.nitro_fuel + config.PLAYER_NITRO_RECHARGE * recharge_time,
            )
            if not nitro_pressed and self.nitro_fuel >= config.PLAYER_NITRO_RESTART_FUEL:
                self.nitro_locked = False

            speed = self.velocity.length()
            if moving and speed > config.PLAYER_MAX_SPEED:
                # Ease out of nitro without keeping its extra speed forever.
                brake_time = min(move_time, (speed - config.PLAYER_MAX_SPEED) / config.PLAYER_STOP_SPEED)
                next_speed = max(config.PLAYER_MAX_SPEED, speed - config.PLAYER_STOP_SPEED * brake_time)
                distance = (speed + next_speed) * brake_time / 2
                distance += config.PLAYER_MAX_SPEED * (move_time - brake_time)
                self.velocity = movement * next_speed
                self.position += movement * distance
            elif moving:
                speed = min(
                    config.PLAYER_MAX_SPEED,
                    speed + config.PLAYER_ACCELERATION * move_time,
                )
                self.velocity = movement * speed
                self.position += self.velocity * move_time
            else:
                # A short stop feels responsive without leaving endless drift.
                brake_time = min(move_time, speed / config.PLAYER_STOP_SPEED)
                next_speed = max(0, speed - config.PLAYER_STOP_SPEED * brake_time)
                if speed > 0:
                    self.position += self.velocity / speed * ((speed + next_speed) * brake_time / 2)
                if next_speed == 0:
                    self.velocity.update(0, 0)
                else:
                    self.velocity.scale_to_length(next_speed)

        self.thrusting = moving or self.nitro_active
        if self.thrusting:
            self.animation_time += dt
        else:
            self.animation_time = 0

        # Move old shots and remove them after a short time.
        for laser in self.lasers[:]:
            laser["previous_position"] = laser["position"].copy()
            laser["position"] += laser["velocity"] * dt
            laser["time_left"] -= dt
            if laser["time_left"] <= 0:
                self.lasers.remove(laser)

        self.shoot_timer = max(0, self.shoot_timer - dt)
        if shooting and self.shoot_timer == 0 and aim.length_squared() > 0:
            self.shoot(aim)

    def shoot(self, direction):
        # Each shot remembers where it is and which way it is travelling.
        laser = {
            "position": self.position + direction * 65,
            "previous_position": self.position + direction * 65,
            "velocity": direction * config.LASER_SPEED,
            "direction": direction,
            "time_left": config.LASER_LIFETIME,
        }
        self.lasers.append(laser)
        self.shoot_timer = config.LASER_COOLDOWN
        if self.rapid_fire_timer > 0:
            self.shoot_timer *= 0.5
        if self.laser_sound is not None:
            try:
                self.laser_sound.play()
            except pygame.error:
                self.laser_sound = None

    def take_damage(self, damage):
        # A short safe period stops one collision from draining all your health.
        if self.hit_timer == 0 and self.health > 0:
            self.health = max(0, self.health - damage)
            self.hit_timer = config.PLAYER_HIT_COOLDOWN
            if self.health == 0:
                self.stop_nitro()
            return True
        return False

    def draw(self, screen):
        # Convert each shot's world position into a position on the screen.
        center = pygame.Vector2(screen.get_rect().center)
        for laser in self.lasers:
            tip = laser["position"] - self.position + center
            tail = tip - laser["direction"] * config.LASER_LENGTH
            pygame.draw.line(screen, config.LASER_COLOR, tail, tip, 5)
            pygame.draw.line(screen, (225, 255, 255), tail, tip, 2)

        # The explosion replaces a destroyed ship. Shots still stay visible.
        if self.health <= 0:
            return

        # Short exhaust streaks follow turns instead of drawing a shield.
        for position, direction, age in self.nitro_trail:
            fade = 1 - age / 0.22
            tip = position - self.position + center - direction * 40
            tail = tip - direction * (35 + 35 * fade)
            orange = (int(240 * fade), int(105 * fade), int(30 * fade))
            blue = (int(100 * fade), int(200 * fade), int(255 * fade))
            pygame.draw.line(screen, orange, tail, tip, max(1, int(10 * fade)))
            pygame.draw.line(screen, blue, tail, tip, max(1, int(3 * fade)))
        if self.nitro_active:
            side = self.nitro_direction.rotate(90) * 17
            length = 60 + int(self.animation_time * 80) % 20
            for offset in (-side, side):
                tip = center - self.nitro_direction * 40 + offset
                tail = tip - self.nitro_direction * length
                pygame.draw.line(screen, (255, 145, 45), tail, tip, 9)
                pygame.draw.line(screen, (145, 225, 255), tail, tip, 3)

        # Blink briefly after being hit.
        if self.hit_timer > 0 and int(self.hit_timer * 10) % 2 == 0:
            return

        image = self.idle_image
        frame_number = -1
        if self.thrusting:
            frame_number = int(self.animation_time / config.FRAME_TIME)
            frame_number %= len(self.frames)
            image = self.frames[frame_number]

        # Reuse the last rotation until the angle or animation frame changes.
        angle = round(self.angle) % 360
        rotation_key = (frame_number, angle)
        if rotation_key != self.rotation_key:
            # Negative rotation makes positive angles turn clockwise on screen.
            self.rotated_image = pygame.transform.rotate(image, -angle)
            self.rotation_key = rotation_key

        image_rect = self.rotated_image.get_rect(center=screen.get_rect().center)
        screen.blit(self.rotated_image, image_rect)
