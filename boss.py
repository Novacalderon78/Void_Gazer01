import math
import random
import pygame
import config


FRAME_SIZE = 220
FRAME_TIME = 0.08
DEATH_FRAME_TIME = 0.08
art = {}


def load_frames(name):
    # These strips were made from the boss GIFs already in game_sprites/boss.
    if name not in art:
        path = config.GAME_FOLDER / "game_sprites/boss" / (name + ".png")
        strip = pygame.image.load(str(path)).convert_alpha()
        art[name] = [
            strip.subsurface((x, 0, FRAME_SIZE, FRAME_SIZE)).copy()
            for x in range(0, strip.get_width(), FRAME_SIZE)
        ]
    return art[name]


def load_death_frames():
    return load_frames("boss_death")


def preload():
    for name in ("boss_idle", "boss_fire", "boss_death"):
        load_frames(name)
    for name in ("boss_idle", "boss_fire"):
        if name + "_flash" not in art:
            frames = []
            for frame in art[name]:
                flash = frame.copy()
                flash.fill((110, 110, 110, 0), special_flags=pygame.BLEND_RGBA_ADD)
                frames.append(flash)
            art[name + "_flash"] = frames


class Boss:
    def __init__(self, position, level=1):
        preload()
        self.position = pygame.Vector2(position)
        self.arena_center = self.position + pygame.Vector2(0, config.BOSS_ENTRY_DISTANCE)
        self.arena_radius = 720
        self.arena_outside_time = 0
        self.previous_position = self.position.copy()
        self.kind = "boss"
        self.level = max(1, int(level))
        self.name = "VOID REAVER"
        self.max_health = config.BOSS_HEALTH + min(120, (self.level - 1) * 20)
        self.health = self.max_health
        self.score = config.BOSS_SCORE
        self.radius = 84
        self.color = (155, 235, 110)
        self.bonus = False
        self.escaped = False
        self.animation_time = 0
        self.hit_timer = 0
        self.warning = False
        self.phase = 1
        self.phase_name = "HUNTER"
        self.phase_changed = False
        self.transition_timer = 0
        self.phase_flash = 0
        self.enraged = False
        self.approach_time = 2.0
        self.intro_duration = self.approach_time + 2.0
        self.intro_timer = self.intro_duration
        self.arrival_target = self.position.copy()
        self.arrival_offset = pygame.Vector2(0, -config.BOSS_ENTRY_DISTANCE)
        self.arrival_distance = config.HEIGHT / 2 + FRAME_SIZE * 1.25
        self.arrival_time = 1.25
        self.arrival_landed = False
        self.impact_duration = 0.55
        self.impact_timer = 0
        self.position.y -= self.arrival_distance
        self.previous_position = self.position.copy()
        self.can_take_damage = False
        self.contact_start_fraction = 0
        self.state = "intro"
        self.timer = self.intro_timer
        self.attack_number = 0
        self.attack_bag = []
        self.attack_bag_phase = 0
        self.last_attack_name = ""
        self.orbit_direction = 0
        self.orbit_time = 0
        self.orbit_angular_velocity = 0
        self.flee_time = 0
        self.boss_velocity = pygame.Vector2()
        self.last_ai_position = self.position.copy()
        self.support_timer = 2.7
        self.support_number = 0
        self.attack_name = "INCOMING"
        self.attack_direction = pygame.Vector2(0, 1)
        self.shot_directions = []
        self.volleys_left = 0
        self.charges_left = 0
        self.ring_turn = 0
        self.mine_positions = []
        self.portal_positions = []
        self.portal_directions = []
        self.crossfire_timer = 0
        self.starfall_positions = []
        self.starfall_targets = []
        self.lance_positions = []
        self.lance_length = 1300
        self.lance_width = 44
        self.rift_target = self.position.copy()
        self.rift_gap_direction = pygame.Vector2(0, 1)
        self.rift_warning_duration = 1.05
        self.rift_shadow = art["boss_idle"][0].copy()
        self.rift_shadow.set_alpha(65)
        self.blade_origin = self.position.copy()
        self.spiral_angle = 0
        self.spiral_timer = 0
        self.beam_active = False
        self.beam_was_active = False
        self.beam_active_start_fraction = 0
        self.beam_active_end_fraction = 0
        self.beam_warning = False
        self.beam_start = self.position.copy()
        self.beam_end = self.position.copy()
        self.beam_previous_start = self.beam_start.copy()
        self.beam_previous_end = self.beam_end.copy()
        self.beam_width = 34
        self.beam_length = config.BOSS_LASER_RANGE
        self.beam_warning_duration = 1.65
        self.beam_duration = 2.3
        self.beam_sweep_angle = 180
        self.beam_sweep_speed = self.beam_sweep_angle / self.beam_duration
        self.beam_track_timer = 0
        self.beam_sweep_sign = 1
        self.beam_center_direction = pygame.Vector2(0, 1)
        self.firing_time = 0
        self.firing_animation = 0
        self.labels = {}

    def aim_at(self, player):
        lead = player.velocity * 0.2
        if lead.length_squared() > 100 * 100:
            lead.scale_to_length(100)
        direction = player.position + lead - self.position
        if direction.length_squared() == 0:
            return pygame.Vector2(0, 1)
        return direction.normalize()

    def prepare_attack(self, player):
        if self.phase == 1:
            attacks = ("HOMING FAN", "VOID RING", "RIFT AMBUSH", "CHARGE", "REAPER BLADES", "STARFALL")
        else:
            attacks = ("SPIRAL", "CROSSFIRE", "ION STORM", "REAPER BLADES", "DEATHRAY", "RIFT AMBUSH",
                       "VOID MINES", "STARFALL", "CHARGE", "HOMING FAN", "VOID RING")
        if self.attack_bag_phase != self.phase or not self.attack_bag:
            self.attack_bag = list(attacks)
            self.attack_bag_phase = self.phase
        choices = [name for name in self.attack_bag if name != self.last_attack_name]
        if not choices:
            self.attack_bag = list(attacks)
            choices = [name for name in self.attack_bag if name != self.last_attack_name]
        outside = self.position.distance_to(self.arena_center) > self.arena_radius + 200
        player_inside = player.position.distance_to(self.arena_center) <= self.arena_radius
        if outside and player_inside and self.last_attack_name != "RIFT AMBUSH":
            if "RIFT AMBUSH" not in self.attack_bag:
                self.attack_bag.append("RIFT AMBUSH")
            choices = ["RIFT AMBUSH"]
        distance = self.position.distance_to(player.position)
        weights = []
        for name in choices:
            weight = 1.0
            if (distance > 550 or self.flee_time > 0.75) and name in ("CHARGE", "RIFT AMBUSH", "ION STORM"):
                weight += 4
            if self.orbit_time > 0.9 and name in ("CROSSFIRE", "ION STORM", "RIFT AMBUSH", "REAPER BLADES"):
                weight += 4
            if distance < 210 and name in ("VOID RING", "REAPER BLADES", "RIFT AMBUSH"):
                weight += 4
            weights.append(weight)
        self.attack_name = random.choices(choices, weights=weights, k=1)[0]
        self.attack_bag.remove(self.attack_name)
        self.last_attack_name = self.attack_name
        self.attack_number += 1
        self.volleys_left = 3 if self.phase == 3 else 2
        self.charges_left = self.phase + 2
        self.ring_turn = 0
        self.begin_warning(player)

    def begin_warning(self, player, followup=False):
        # Each volley or dash gets its own warning, with a locked direction.
        self.attack_direction = self.aim_at(player)
        self.shot_directions = []
        self.mine_positions = []
        self.portal_positions = []
        self.portal_directions = []
        self.starfall_positions = []
        self.starfall_targets = []
        self.lance_positions = []
        self.can_take_damage = self.intro_timer == 0 and self.health > 0
        self.beam_active = False
        self.beam_warning = False
        if self.attack_name == "HOMING FAN":
            count = 10 + self.phase * 2
            for index in range(count):
                angle = (index - (count - 1) / 2) * 11
                self.shot_directions.append(self.attack_direction.rotate(angle))
            self.timer = 0.3 if followup else 0.65
        elif self.attack_name == "VOID RING":
            self.attack_direction = self.attack_direction.rotate(self.ring_turn)
            count = 24 + self.phase * 2
            for index in range(count):
                angle = index * 360 / count
                # The second ring turns its escape gap. Both gaps are shown.
                if min(angle, 360 - angle) > 30:
                    self.shot_directions.append(self.attack_direction.rotate(angle))
            self.ring_turn += 34
            self.timer = 0.5 if followup else 0.7
        elif self.attack_name == "CHARGE":
            lead = player.velocity * 0.4
            if lead.length_squared() > 180 * 180:
                lead.scale_to_length(180)
            direction = player.position + lead - self.position
            if direction.length_squared() > 0:
                self.attack_direction = direction.normalize()
            self.timer = 0.34 if followup else 0.65
        elif self.attack_name == "SPIRAL":
            self.spiral_angle = pygame.Vector2(1, 0).angle_to(self.attack_direction)
            self.spiral_timer = 0
            self.timer = 0.85
        elif self.attack_name == "VOID MINES":
            # Mark the locations before the mines arrive, then give each a fuse.
            target = player.position + player.velocity * 0.18
            count = 5 if self.phase == 2 else 7
            for index in range(count):
                angle = index * 360 / count + self.attack_number * 23
                radius = 165 if index % 2 == 0 else 260
                self.mine_positions.append(target + pygame.Vector2(radius, 0).rotate(angle))
            self.timer = 0.8
        elif self.attack_name == "CROSSFIRE":
            target = player.position + player.velocity * 0.18
            side = self.attack_direction.rotate(90)
            self.portal_positions = [target + side * distance for distance in (-720, 720)]
            self.aim_portals(player)
            self.volleys_left = 5
            self.crossfire_timer = 0
            self.timer = 0.8
        elif self.attack_name == "STARFALL":
            target = player.position + player.velocity * 0.3
            count = 8 if self.phase == 3 else 6
            spacing = 120 if self.phase == 3 else 140
            for index in range(count):
                x = target.x + (index - (count - 1) / 2) * spacing
                y = target.y - 650 - (index % 3) * 110
                position = pygame.Vector2(x, y)
                self.starfall_positions.append(position)
                self.starfall_targets.append(position + pygame.Vector2(0, 620 * 0.85))
            self.timer = 0.85
        elif self.attack_name == "ION STORM":
            target = player.position + player.velocity * 0.25
            count = 5 if self.phase == 3 else 3
            for index in range(count):
                x = target.x + (index - (count - 1) / 2) * 180
                self.lance_positions.append(pygame.Vector2(x, target.y - 650))
            self.timer = 1.05
        elif self.attack_name == "RIFT AMBUSH":
            lead = player.velocity * 0.45
            if lead.length_squared() > 180 * 180:
                lead.scale_to_length(180)
            self.rift_target = player.position + lead
            offset = self.rift_target - self.arena_center
            maximum = max(1, self.arena_radius - 140)
            if offset.length_squared() > maximum * maximum:
                self.rift_target = self.arena_center + offset.normalize() * maximum
            direction = player.position - self.rift_target
            self.rift_gap_direction = direction.normalize() if direction.length_squared() else self.attack_direction.copy()
            count = 12 if self.phase == 1 else 16
            for index in range(count):
                angle = 45 + index * 270 / (count - 1)
                self.shot_directions.append(self.rift_gap_direction.rotate(angle))
            self.can_take_damage = False
            self.timer = self.rift_warning_duration
        elif self.attack_name == "REAPER BLADES":
            self.blade_origin = self.position.copy()
            count = 4 + self.phase * 2
            for index in range(count):
                self.shot_directions.append(self.attack_direction.rotate(index * 360 / count))
            self.timer = 0.9
        else:  # DEATHRAY
            self.timer = self.beam_warning_duration
            self.beam_track_timer = 0.3
            self.beam_sweep_sign = -self.orbit_direction if self.orbit_time > 0.9 else -self.beam_sweep_sign
            self.beam_center_direction = self.attack_direction.copy()
            self.attack_direction = self.beam_center_direction.rotate(-90 * self.beam_sweep_sign)
            self.beam_length = max(config.BOSS_LASER_RANGE, self.position.distance_to(player.position) + 1600)
            self.beam_warning = True
            self.update_beam()
        self.state = "warning"
        self.warning = True

    def update_beam(self):
        self.beam_start = self.position + self.attack_direction * (self.radius + 6)
        self.beam_end = self.beam_start + self.attack_direction * self.beam_length

    def finish_attack(self):
        self.state = "waiting"
        self.attack_name = "RECOVERING"
        self.warning = False
        self.beam_warning = False
        self.beam_active = False
        self.shot_directions = []
        self.mine_positions = []
        self.portal_positions = []
        self.portal_directions = []
        self.starfall_positions = []
        self.starfall_targets = []
        self.lance_positions = []
        self.volleys_left = 0
        self.charges_left = 0
        self.can_take_damage = self.intro_timer == 0 and self.health > 0
        self.timer = (0.50, 0.35, 0.25)[self.phase - 1] * (0.7 if self.enraged else 1)

    def bullet_room(self, bullets):
        return max(0, config.BOSS_BULLET_LIMIT - sum(shot.get("boss", False) for shot in bullets))

    def fire(self, bullets):
        # A limit also protects performance if another caller forgets to expire shots.
        available = self.bullet_room(bullets)
        homing = self.attack_name == "HOMING FAN"
        speed = (345 if not homing else 370) + self.phase * 15
        if self.attack_name == "RIFT AMBUSH":
            speed = 310 + self.phase * 30
        speed += min(30, (self.level - 1) * 5)
        for direction in self.shot_directions[:available]:
            shot = {
                "position": self.position + direction * (self.radius + 10),
                "velocity": direction * speed,
                "time_left": 3.2 if self.attack_name == "RIFT AMBUSH" else 3.5,
                "color": self.color,
                "damage": 1,
                "radius": 7 if homing or self.attack_name == "RIFT AMBUSH" else 6,
                "boss": True,
            }
            if homing:
                # Tracking stops early; the player can out-turn the locked shots.
                shot["homing_timer"] = 1.1 if self.phase == 1 else 1.3
                shot["turn_speed"] = 65
            bullets.append(shot)
        self.firing_time = 0.8
        self.firing_animation = 0

    def fire_spiral(self, bullets):
        count = 4 if self.phase == 3 else 3
        for index in range(min(count, self.bullet_room(bullets))):
            direction = pygame.Vector2(1, 0).rotate(self.spiral_angle + index * 360 / count)
            bullets.append({
                "position": self.position + direction * (self.radius + 12),
                "velocity": direction * (315 + self.phase * 20),
                "time_left": 3.2,
                "color": (210, 115, 255),
                "damage": 1,
                "radius": 6,
                "boss": True,
            })
        self.spiral_angle += 17 if self.phase == 2 else 19
        self.firing_time = 0.3

    def drop_mines(self, bullets):
        for position in self.mine_positions[:self.bullet_room(bullets)]:
            bullets.append({
                "position": position.copy(),
                "velocity": pygame.Vector2(),
                "time_left": 4,
                "color": (245, 115, 235),
                "damage": 1,
                "radius": 12,
                "boss": True,
                "mine": True,
                "fuse": 1.2,
                "burst_count": 8 if self.phase == 2 else 10,
                "burst_speed": 285,
            })
        self.firing_time = 0.6
        self.firing_animation = 0

    def aim_portals(self, player):
        target = player.position + player.velocity * 0.18
        self.portal_directions = []
        for position in self.portal_positions:
            direction = target - position
            if direction.length_squared() == 0:
                direction = pygame.Vector2(0, 1)
            self.portal_directions.append(direction.normalize())

    def fire_crossfire(self, player, bullets):
        self.aim_portals(player)
        count = 5 if self.phase == 3 else 3
        available = self.bullet_room(bullets)
        for position, aim in zip(self.portal_positions, self.portal_directions):
            for index in range(count):
                if available <= 0:
                    break
                direction = aim.rotate((index - (count - 1) / 2) * 10)
                bullets.append({
                    "position": position.copy(),
                    "velocity": direction * 480,
                    "time_left": 3.2,
                    "color": (110, 210, 255),
                    "damage": 1,
                    "radius": 6,
                    "boss": True,
                })
                available -= 1
        self.firing_time = 0.35
        self.firing_animation = 0

    def fire_starfall(self, bullets):
        for position in self.starfall_positions[:self.bullet_room(bullets)]:
            bullets.append({
                "position": position.copy(),
                "velocity": pygame.Vector2(0, 620),
                "time_left": 3,
                "color": (255, 165, 80),
                "damage": 1,
                "radius": 9,
                "boss": True,
                "meteor": True,
                "split_timer": 0.85,
                "split_count": 6,
                "split_speed": 300,
            })
        self.firing_time = 0.6
        self.firing_animation = 0

    def fire_ion_storm(self, bullets, spawn_delay):
        for position in self.lance_positions[:self.bullet_room(bullets)]:
            bullets.append({
                "position": position.copy(),
                "previous_position": position.copy(),
                "velocity": pygame.Vector2(),
                "direction": pygame.Vector2(0, 1),
                "length": self.lance_length,
                "radius": self.lance_width / 2,
                "time_left": 0.45,
                "damage": 1,
                "color": (205, 115, 255),
                "boss": True,
                "strike": True,
                "spawn_delay": spawn_delay,
            })
        self.impact_timer = max(self.impact_timer, 0.18)
        self.firing_time = 0.6
        self.firing_animation = 0

    def fire_blades(self, bullets, spawn_delay):
        for direction in self.shot_directions[:self.bullet_room(bullets)]:
            bullets.append({
                "position": self.blade_origin + direction * (self.radius + 10),
                "velocity": direction * 460,
                "time_left": 2.4,
                "color": (255, 125, 190),
                "damage": 1,
                "radius": 10,
                "boss": True,
                "blade": True,
                "return_timer": 0.65,
                "return_speed": 520,
                "return_target": self.blade_origin.copy(),
                "spawn_delay": spawn_delay,
            })
        self.firing_time = 0.7
        self.firing_animation = 0

    def track_player(self, player, dt):
        self.boss_velocity = (self.position - self.last_ai_position) / dt
        self.last_ai_position = self.position.copy()
        offset = player.position - self.position
        distance = offset.length()
        if distance == 0:
            return
        direction = offset / distance
        sideways = direction.cross(player.velocity)
        along = direction.dot(player.velocity)
        angular_speed = math.degrees(sideways / distance)
        self.orbit_angular_velocity += (angular_speed - self.orbit_angular_velocity) * min(1, dt * 8)
        if abs(sideways) > 140 and abs(sideways) > abs(along) * 0.75:
            sign = 1 if sideways > 0 else -1
            self.orbit_time = min(10, self.orbit_time + dt) if sign == self.orbit_direction else dt
            self.orbit_direction = sign
        else:
            self.orbit_time = max(0, self.orbit_time - dt * 2)
            if self.orbit_time == 0:
                self.orbit_direction = 0
        self.flee_time = min(5, self.flee_time + dt) if distance > 550 else max(0, self.flee_time - dt)

    def support_target(self, player):
        # Predict where an unchanged flight path will be when the marker arms.
        if self.orbit_time > 0.65:
            offset = player.position - self.position
            target = self.position + offset.rotate(self.orbit_angular_velocity * 0.85)
            lead = self.boss_velocity * 0.85
            if lead.length_squared() > 100 * 100:
                lead.scale_to_length(100)
            return target + lead
        lead = player.velocity * 0.85
        if lead.length_squared() > 330 * 330:
            lead.scale_to_length(330)
        return player.position + lead

    def fire_support(self, player, bullets, spawn_delay):
        target = self.support_target(player)
        direction = player.velocity.normalize() if player.velocity.length_squared() else self.aim_at(player)
        side = direction.rotate(90)
        sign = 1 if self.support_number % 2 == 0 else -1
        candidates = [target,
                      target + side * (150 * sign) + direction * 250,
                      target - side * (150 * sign) - direction * 250,
                      target - side * (310 * sign) + direction * 180]
        # Extra choices keep the promised gaps when the arena edge shifts a marker.
        for angle in range(0, 360, 30):
            candidates.append(target + pygame.Vector2(310, 0).rotate(angle))
        positions = []
        danger_radius = 72 + config.PLAYER_HIT_RADIUS
        exits = [player.position + pygame.Vector2(180, 0).rotate(angle) for angle in range(0, 360, 45)]
        amount = min(self.phase + 1, self.bullet_room(bullets))
        for candidate in candidates:
            offset = candidate - self.arena_center
            maximum = max(1, self.arena_radius - 90)
            if offset.length_squared() > maximum * maximum:
                candidate = self.arena_center + offset.normalize() * maximum
            if any(candidate.distance_to(other) < danger_radius * 2 + 70 for other in positions):
                continue
            blocked = positions + [candidate]
            if not any(all(exit.distance_to(mark) > danger_radius for mark in blocked) for exit in exits):
                continue
            positions.append(candidate.copy())
            if len(positions) >= amount:
                break
        for position in positions:
            bullets.append({
                "position": position,
                "previous_position": position.copy(),
                "velocity": pygame.Vector2(),
                "time_left": 1.3,
                "color": (255, 110, 60),
                "damage": 1,
                "radius": 72,
                "boss": True,
                "trap": True,
                "arm_timer": 0.85,
                "blast_timer": 0.35,
                "spawn_delay": spawn_delay,
            })
        self.support_number += 1

    def update_support(self, dt, player, bullets, elapsed):
        interval = (2.7, 2.1, 1.6)[self.phase - 1]
        self.support_timer = min(self.support_timer, interval)
        left = dt
        while left > 0:
            step = min(left, self.support_timer)
            self.support_timer = max(0, self.support_timer - step)
            left -= step
            if self.support_timer <= 0.000000001:
                self.fire_support(player, bullets, max(0, elapsed + dt - left))
                self.support_timer = interval

    def move(self, dt, player):
        difference = player.position - self.position
        distance = difference.length()
        if distance == 0:
            return
        direction = difference / distance
        if distance > 580:
            # Keep the fight nearby if the player flies away.
            self.position += direction * 510 * dt
        else:
            approach = max(-145, min(190, (distance - 340) * 1.1))
            orbit = direction.rotate(90) * (65 + self.phase * 15)
            self.position += (direction * approach + orbit) * dt

    def arrive(self, dt, player):
        # Follow the camera during the entrance so the drop stays on screen.
        self.arrival_target = player.position + self.arrival_offset
        elapsed = self.intro_duration - self.intro_timer
        next_elapsed = elapsed + dt - self.approach_time
        progress = max(0, min(1, next_elapsed / self.arrival_time))
        self.position = self.arrival_target + pygame.Vector2(
            0, -self.arrival_distance * (1 - progress * progress)
        )
        if next_elapsed > 0 and not self.arrival_landed:
            self.attack_name = "ARRIVING"
        if not self.arrival_landed and next_elapsed >= self.arrival_time - 0.000000001:
            self.arrival_landed = True
            # Keep the impact's duration equal at different frame rates.
            self.impact_timer = max(0, self.impact_duration - (next_elapsed - self.arrival_time))
            self.attack_name = "LANDED"

    def update(self, dt, player, bullets):
        self.phase_changed = False
        if self.health <= 0:
            self.can_take_damage = False
            self.beam_active = False
            self.beam_was_active = False
            self.beam_active_start_fraction = 0
            self.beam_active_end_fraction = 0
            self.beam_warning = False
            self.warning = False
            self.impact_timer = 0
            return
        if dt <= 0:
            return
        self.contact_start_fraction = 0
        self.beam_was_active = self.beam_active
        # Fractions describe only the part of this update when the ray hurts.
        self.beam_active_start_fraction = 0
        self.beam_active_end_fraction = 0
        self.beam_previous_start = self.beam_start.copy()
        self.beam_previous_end = self.beam_end.copy()
        self.animation_time += dt
        self.phase_flash = max(0, self.phase_flash - dt)
        self.impact_timer = max(0, self.impact_timer - dt)
        self.firing_time = max(0, self.firing_time - dt)
        if self.firing_time > 0:
            self.firing_animation += dt
        self.enraged = self.health <= self.max_health * 0.15
        if self.intro_timer == 0:
            self.track_player(player, dt)

        if self.beam_active or self.beam_warning:
            # Flying away never cuts a committed ray short or puts it out of range.
            self.beam_length = max(config.BOSS_LASER_RANGE, self.position.distance_to(player.position) + 1600)
            self.update_beam()

        next_phase = 1 if self.health > self.max_health * 2 / 3 else 2
        if self.health <= self.max_health / 3:
            next_phase = 3
        committed_ray = self.attack_name == "DEATHRAY" and self.state in ("warning", "beaming")
        if next_phase != self.phase and self.intro_timer == 0 and not committed_ray:
            self.phase = next_phase
            self.phase_name = ("HUNTER", "EXPOSED CORE", "FINAL FURY")[self.phase - 1]
            self.phase_changed = True
            self.color = ((155, 235, 110), (255, 185, 80), (255, 90, 100))[self.phase - 1]
            self.phase_flash = 1.1
            self.finish_attack()
            self.attack_number = 0
            self.attack_name = self.phase_name
            self.state = "transition"
            self.can_take_damage = False
            self.timer = 1.1
            self.transition_timer = self.timer
            self.beam_was_active = False

        distance = self.position.distance_to(player.position)
        committed_crossfire = self.attack_name == "CROSSFIRE" and self.state in ("warning", "crossfire")
        committed_warning = self.attack_name in ("RIFT AMBUSH", "ION STORM", "REAPER BLADES") and self.state == "warning"
        if self.intro_timer == 0 and (
            self.state == "pursuing" or
            (distance > 800 and self.state not in ("charging", "beaming", "transition")
             and not committed_ray and not committed_crossfire and not committed_warning)
        ):
            if self.state != "pursuing":
                self.finish_attack()
                self.state = "pursuing"
                self.attack_name = "PURSUING"
            # Stay in pursuit until close, so warnings cannot trap it far away.
            if distance > 420:
                speed = min(1000, max(850, distance))
                travel = min(speed * dt, distance - 420)
                self.position += (player.position - self.position) / distance * travel
            if self.position.distance_to(player.position) <= 420.001:
                self.state = "waiting"
                self.attack_name = "READY"
                self.timer = 0.1
            self.update_support(dt, player, bullets, 0)
            return

        # Consume leftover time so warnings last equally at 30, 60 and 120 FPS.
        remaining = dt
        while remaining > 0:
            if self.state == "spiraling" and self.spiral_timer <= 0.000000001:
                self.fire_spiral(bullets)
                self.spiral_timer = 0.12
            elif self.state == "crossfire" and self.crossfire_timer <= 0.000000001 and self.volleys_left > 0:
                self.fire_crossfire(player, bullets)
                self.volleys_left -= 1
                self.crossfire_timer = 0.28
            step = min(remaining, max(0, self.timer))
            if self.state == "spiraling":
                step = min(step, self.spiral_timer)
            elif self.state == "crossfire":
                step = min(step, self.crossfire_timer)
            elif self.state == "warning" and self.beam_track_timer > 0 and self.beam_warning:
                step = min(step, self.beam_track_timer)
            if self.state == "intro":
                self.arrive(step, player)
            elif self.state == "waiting":
                self.move(step, player)
            elif self.state == "charging":
                speed = 840 + self.phase * 60
                self.position += self.attack_direction * speed * step
            elif self.state == "spiraling":
                self.spiral_timer = max(0, self.spiral_timer - step)
            elif self.state == "crossfire":
                self.crossfire_timer = max(0, self.crossfire_timer - step)
                self.aim_portals(player)
            elif self.state == "beaming":
                # Sweep from a locked heading. Never follow the player mid-ray.
                self.attack_direction = self.attack_direction.rotate(self.beam_sweep_sign * self.beam_sweep_speed * step)
                self.update_beam()
                self.beam_active_end_fraction = min(1, (dt - remaining + step) / dt)
            elif self.state == "warning" and self.beam_warning:
                if self.beam_track_timer > 0:
                    self.beam_center_direction = self.aim_at(player)
                    self.attack_direction = self.beam_center_direction.rotate(-90 * self.beam_sweep_sign)
                    self.beam_track_timer = max(0, self.beam_track_timer - step)
                    self.update_beam()
            elif self.state == "warning" and self.attack_name == "CROSSFIRE":
                self.aim_portals(player)
            if self.state not in ("intro", "transition"):
                self.update_support(step, player, bullets, dt - remaining)
            self.timer = max(0, self.timer - step)
            if self.timer < 0.000000001:
                self.timer = 0
            remaining -= step
            if self.state == "intro":
                self.intro_timer = self.timer
            elif self.state == "transition":
                self.transition_timer = self.timer
            if self.timer > 0:
                if remaining <= 0:
                    break
                continue
            if self.state == "intro":
                self.can_take_damage = True
                # The descent must never count as a damaging swept collision.
                self.previous_position = self.position.copy()
                self.state = "waiting"
                self.attack_name = "READY"
                self.timer = 0.6
            elif self.state == "transition":
                self.can_take_damage = True
                self.previous_position = self.position.copy()
                self.state = "waiting"
                self.attack_name = "READY"
                self.timer = 0.3
            elif self.state == "waiting":
                self.prepare_attack(player)
            elif self.state == "warning":
                self.warning = False
                if self.attack_name == "CHARGE":
                    self.state = "charging"
                    self.timer = 0.36
                elif self.attack_name == "DEATHRAY":
                    self.beam_warning = False
                    self.beam_active = True
                    self.beam_was_active = True
                    self.beam_previous_start = self.beam_start.copy()
                    self.beam_previous_end = self.beam_end.copy()
                    self.beam_active_start_fraction = min(1, max(0, (dt - remaining) / dt))
                    self.beam_active_end_fraction = self.beam_active_start_fraction
                    self.state = "beaming"
                    self.timer = self.beam_duration
                    self.firing_time = self.beam_duration + 0.12
                    self.firing_animation = 0
                elif self.attack_name == "SPIRAL":
                    self.state = "spiraling"
                    self.timer = 2.0 if self.phase == 2 else 2.4
                    self.spiral_timer = 0
                elif self.attack_name == "VOID MINES":
                    self.drop_mines(bullets)
                    self.finish_attack()
                elif self.attack_name == "CROSSFIRE":
                    self.state = "crossfire"
                    self.timer = 5 * 0.28
                    self.crossfire_timer = 0
                elif self.attack_name == "STARFALL":
                    self.fire_starfall(bullets)
                    self.finish_attack()
                elif self.attack_name == "ION STORM":
                    self.fire_ion_storm(bullets, max(0, dt - remaining))
                    self.finish_attack()
                elif self.attack_name == "REAPER BLADES":
                    self.fire_blades(bullets, max(0, dt - remaining))
                    self.finish_attack()
                elif self.attack_name == "RIFT AMBUSH":
                    self.position = self.rift_target.copy()
                    # Teleporting has no damaging path through the old position.
                    self.previous_position = self.position.copy()
                    self.contact_start_fraction = min(1, max(0, (dt - remaining) / dt))
                    self.can_take_damage = True
                    first_shot = len(bullets)
                    self.fire(bullets)
                    for shot in bullets[first_shot:]:
                        shot["spawn_delay"] = max(0, dt - remaining)
                    self.impact_timer = max(self.impact_timer, 0.28)
                    self.finish_attack()
                    self.timer = 0.5
                else:
                    self.fire(bullets)
                    self.volleys_left -= 1
                    if self.attack_name == "VOID RING":
                        self.volleys_left = min(self.volleys_left, 1)
                    if self.volleys_left > 0:
                        self.begin_warning(player, followup=True)
                    else:
                        self.finish_attack()
            elif self.state == "charging":
                self.charges_left -= 1
                if self.charges_left > 0:
                    self.begin_warning(player, followup=True)
                else:
                    self.finish_attack()
            else:
                self.finish_attack()

    def label(self, font, text):
        key = (id(font), text, self.color)
        if key not in self.labels:
            self.labels[key] = font.render(text, True, self.color)
        return self.labels[key]

    def draw(self, screen, player_position, font):
        # The roar warns the player before any part of the boss is revealed.
        elapsed = self.intro_duration - self.intro_timer
        if self.intro_timer > 0 and elapsed < self.approach_time:
            return
        offset = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2) - player_position
        center = self.position + offset
        # Draw the whole beam even when the boss itself is outside the screen.
        if self.beam_active or self.beam_warning:
            start = self.beam_start + offset
            end = self.beam_end + offset
            if self.beam_active:
                pygame.draw.line(screen, (255, 65, 105), start, end, self.beam_width)
                pygame.draw.line(screen, (255, 210, 150), start, end, 12)
                pygame.draw.line(screen, (255, 255, 240), start, end, 5)
            else:
                side = self.attack_direction.rotate(90) * (self.beam_width / 2)
                for edge in (-1, 1):
                    pygame.draw.line(screen, (255, 100, 120), start + side * edge, end + side * edge, 2)
                pygame.draw.line(screen, (255, 170, 100), start, end, 1)
                for number in range(1, 11):
                    mark = start.lerp(end, number / 11)
                    pygame.draw.circle(screen, (255, 180, 115), (round(mark.x), round(mark.y)), 3)
                # Show the complete sweep, not just the ray's starting line.
                for angle in (-90, 90):
                    direction = self.beam_center_direction.rotate(angle * self.beam_sweep_sign)
                    pygame.draw.line(screen, (150, 75, 85), center + direction * self.radius,
                                     center + direction * self.beam_length, 2)
                player_distance = self.position.distance_to(player_position)
                far_arc = max(1040, player_distance)
                for radius in (260, 520, 780, far_arc):
                    arc = [center + self.beam_center_direction.rotate(angle * self.beam_sweep_sign) * radius
                           for angle in range(-90, 91, 3)]
                    pygame.draw.lines(screen, (115, 65, 80), False, arc, 1)
                arrow = self.beam_center_direction * max(310, min(self.beam_length - 100, player_distance))
                direction = self.beam_center_direction.rotate(90 * self.beam_sweep_sign)
                tip = center + arrow + direction * 38
                pygame.draw.line(screen, (255, 180, 115), center + arrow - direction * 38, tip, 3)
                pygame.draw.line(screen, (255, 180, 115), tip, tip - direction * 15 + self.beam_center_direction * 12, 3)
                pygame.draw.line(screen, (255, 180, 115), tip, tip - direction * 15 - self.beam_center_direction * 12, 3)
        if self.warning and self.attack_name == "VOID MINES":
            for position in self.mine_positions:
                mark = position + offset
                point = (round(mark.x), round(mark.y))
                radius = 26 + round(math.sin(self.animation_time * 14) * 4)
                pygame.draw.circle(screen, (245, 115, 235), point, radius, 2)
                pygame.draw.line(screen, (245, 115, 235), mark + (-10, 0), mark + (10, 0), 2)
                pygame.draw.line(screen, (245, 115, 235), mark + (0, -10), mark + (0, 10), 2)
        if self.attack_name == "CROSSFIRE" and self.state in ("warning", "crossfire"):
            count = 5 if self.phase == 3 else 3
            for position, aim in zip(self.portal_positions, self.portal_directions):
                mark = position + offset
                color = (110, 210, 255)
                radius = 30 + round(math.sin(self.animation_time * 14) * 4)
                pygame.draw.circle(screen, color, mark, radius, 3)
                pygame.draw.circle(screen, color, mark, radius + 11, 1)
                if not screen.get_rect().collidepoint(mark):
                    # Portal arrows stay visible when the portals are off screen.
                    edge = pygame.Vector2(max(32, min(screen.get_width() - 32, mark.x)),
                                          max(150, min(screen.get_height() - 50, mark.y)))
                    direction = (mark - edge).normalize()
                    side = direction.rotate(90)
                    points = [edge + direction * 12,
                              edge - direction * 9 + side * 8,
                              edge - direction * 9 - side * 8]
                    pygame.draw.polygon(screen, color, points)
                    pygame.draw.circle(screen, color, edge, 22, 1)
                for number in range(4):
                    direction = pygame.Vector2(1, 0).rotate(number * 90 + self.animation_time * 100)
                    pygame.draw.line(screen, color, mark + direction * 22, mark + direction * 40, 2)
                for index in range(count):
                    direction = aim.rotate((index - (count - 1) / 2) * 10)
                    line_color = (65, 120, 150) if self.warning else (35, 70, 90)
                    pygame.draw.line(screen, line_color, mark + direction * 35,
                                     mark + direction * (480 * 3.2), 1)
        if self.warning and self.attack_name == "STARFALL":
            color = (255, 165, 80)
            for position, target in zip(self.starfall_positions, self.starfall_targets):
                start, finish = position + offset, target + offset
                for side in (-18, 18):
                    pygame.draw.line(screen, (130, 85, 55), start + (side, 0), finish + (side, 0), 2)
                for number in range(7):
                    mark = start.lerp(finish, number / 6)
                    pygame.draw.line(screen, color, mark + (-6, -8), mark + (0, 0), 2)
                    pygame.draw.line(screen, color, mark + (6, -8), mark + (0, 0), 2)
                radius = 28 + round(math.sin(self.animation_time * 12) * 4)
                pygame.draw.circle(screen, color, finish, radius, 2)
                for angle in range(0, 360, 60):
                    direction = pygame.Vector2(1, 0).rotate(angle)
                    pygame.draw.line(screen, color, finish + direction * (radius + 4),
                                     finish + direction * (radius + 14), 2)
        if self.warning and self.attack_name == "ION STORM":
            for position in self.lance_positions:
                start = position + offset
                end = start + pygame.Vector2(0, self.lance_length)
                color = (205, 115, 255)
                pygame.draw.line(screen, (35, 20, 48), start, end, self.lance_width)
                for side in (-self.lance_width / 2, self.lance_width / 2):
                    pygame.draw.line(screen, color, start + (side, 0), end + (side, 0), 2)
                pygame.draw.circle(screen, color, start, self.lance_width // 2, 2)
                pygame.draw.circle(screen, color, end, self.lance_width // 2, 2)
                for number in range(1, 5):
                    mark = start.lerp(end, number / 5)
                    pygame.draw.line(screen, color, mark + (-12, -12), mark + (12, 12), 2)
                    pygame.draw.line(screen, color, mark + (-12, 12), mark + (12, -12), 2)
        if self.warning and self.attack_name == "RIFT AMBUSH":
            mark = self.rift_target + offset
            progress = max(0, min(1, 1 - self.timer / self.rift_warning_duration))
            color = (195, 115, 255)
            screen.blit(self.rift_shadow, self.rift_shadow.get_rect(center=(round(mark.x), round(mark.y))))
            pygame.draw.circle(screen, color, mark, self.radius, 2)
            pygame.draw.circle(screen, color, mark, self.radius + config.PLAYER_HIT_RADIUS, 2)
            pygame.draw.circle(screen, color, mark, round(self.radius + 65 * (1 - progress)), 1)
            for angle in range(0, 360, 45):
                direction = pygame.Vector2(1, 0).rotate(angle + self.animation_time * 100)
                pygame.draw.line(screen, color, mark + direction * (self.radius - 8),
                                 mark + direction * (self.radius + 15), 3)
            for direction in self.shot_directions:
                pygame.draw.line(screen, color, mark + direction * (self.radius + 12),
                                 mark + direction * 190, 1)
            for angle in (-45, 45):
                direction = self.rift_gap_direction.rotate(angle)
                pygame.draw.line(screen, (110, 245, 185), mark, mark + direction * 240, 2)
        if self.warning and self.attack_name == "REAPER BLADES":
            origin = self.blade_origin + offset
            color = (255, 125, 190)
            for direction in self.shot_directions:
                side = direction.rotate(90)
                start = origin + direction * (self.radius + 10)
                turn = origin + direction * (self.radius + 10 + 460 * 0.65)
                for edge in (-10, 10):
                    pygame.draw.line(screen, (135, 60, 105), start + side * edge, turn + side * edge, 1)
                pygame.draw.circle(screen, color, turn, 11, 2)
                # Separate arrows show the outward pass and the returning pass.
                for distance, travel, lane in ((285, direction, 0), (210, -direction, 16)):
                    mark = origin + direction * distance + side * lane
                    tip = mark + travel * 12
                    pygame.draw.line(screen, color, mark - travel * 12, tip, 2)
                    pygame.draw.line(screen, color, tip, tip - travel * 10 + side * 7, 2)
                    pygame.draw.line(screen, color, tip, tip - travel * 10 - side * 7, 2)
        if not screen.get_rect().inflate(700, 700).collidepoint(center):
            return
        point = (round(center.x), round(center.y))
        if self.intro_timer > 0 and not self.arrival_landed:
            # The full-size sprite falls faster as it approaches the arena.
            progress = max(0, min(1, (elapsed - self.approach_time) / self.arrival_time))
            trail_length = round(30 + progress * 150)
            for side in (-76, 0, 76):
                start = center + pygame.Vector2(side, -65)
                end = start - pygame.Vector2(0, trail_length)
                pygame.draw.line(screen, (35, 75, 60), start, end, 9)
                pygame.draw.line(screen, (110, 205, 140), start, end, 2)
        if self.impact_timer > 0:
            impact = 1 - self.impact_timer / self.impact_duration
            brightness = 1 - impact
            color = (round(150 * brightness), round(240 * brightness), round(180 * brightness))
            radius = round(105 + impact * 260)
            pygame.draw.circle(screen, color, point, radius, max(1, round(7 * brightness)))
            pygame.draw.circle(screen, color, point, round(95 + impact * 170), 2)
            for angle in range(0, 360, 24):
                direction = pygame.Vector2(1, 0).rotate(angle)
                start = center + direction * (90 + impact * 225)
                end = start + direction * (10 + 22 * brightness)
                pygame.draw.line(screen, color, start, end, max(1, round(4 * brightness)))
            if impact < 0.3:
                pygame.draw.circle(screen, (220, 255, 225), point, round(115 + impact * 90), 5)
        pulse = int(math.sin(self.animation_time * 8) * 4)
        if self.intro_timer > 0 or self.warning or self.phase_flash > 0:
            pygame.draw.circle(screen, self.color, point, self.radius + 16 + pulse, 2)
            for angle in range(0, 360, 60):
                direction = pygame.Vector2(1, 0).rotate(angle + self.animation_time * 35)
                mark = center + direction * (self.radius + 24)
                pygame.draw.circle(screen, self.color, (round(mark.x), round(mark.y)), 3)

        if self.transition_timer > 0:
            progress = 1 - self.transition_timer / 1.1
            for index in range(3):
                radius = round(self.radius + 18 + (progress * 180 + index * 55) % 190)
                pygame.draw.circle(screen, self.color, point, radius, 2)
            for angle in range(0, 360, 30):
                direction = pygame.Vector2(1, 0).rotate(angle + self.animation_time * 95)
                pygame.draw.line(screen, self.color, center + direction * (self.radius + 8),
                                 center + direction * (self.radius + 30 + progress * 75), 3)
        elif self.phase > 1:
            # Small orbiting energy cores make later phases visibly different.
            for number in range(self.phase + 1):
                angle = self.animation_time * (65 if self.enraged else 40) + number * 360 / (self.phase + 1)
                mark = center + pygame.Vector2(self.radius + 19, 0).rotate(angle)
                pygame.draw.circle(screen, self.color, (round(mark.x), round(mark.y)), 5)
                pygame.draw.circle(screen, (255, 245, 225), (round(mark.x), round(mark.y)), 2)

        if self.warning:
            if self.attack_name == "CHARGE":
                distance = (840 + self.phase * 60) * 0.36
                end = center + self.attack_direction * distance
                side = self.attack_direction.rotate(90) * self.radius
                for edge in (-1, 1):
                    start = center + side * edge
                    finish = end + side * edge
                    pygame.draw.line(screen, self.color, start, finish, 2)
                pygame.draw.line(screen, self.color, end - side, end + side, 2)
            elif self.attack_name == "SPIRAL":
                count = 4 if self.phase == 3 else 3
                for number in range(count):
                    angle = self.spiral_angle + number * 360 / count
                    direction = pygame.Vector2(1, 0).rotate(angle)
                    start = center + direction * (self.radius + 14)
                    end = center + direction * 240
                    pygame.draw.line(screen, (210, 115, 255), start, end, 2)
                    pygame.draw.circle(screen, (210, 115, 255), (round(end.x), round(end.y)), 7, 2)
            elif self.attack_name not in ("DEATHRAY", "RIFT AMBUSH", "REAPER BLADES"):
                for direction in self.shot_directions:
                    start = center + direction * (self.radius + 10)
                    end = center + direction * (self.radius + 60)
                    pygame.draw.line(screen, self.color, start, end, 2)
                if self.attack_name == "VOID RING":
                    for angle in (-30, 30):
                        end = center + self.attack_direction.rotate(angle) * 230
                        pygame.draw.line(screen, (115, 245, 195), center, end, 2)

        name = "boss_fire" if self.firing_time > 0 else "boss_idle"
        time = self.firing_animation if self.firing_time > 0 else self.animation_time
        if self.hit_timer > 0 or (self.transition_timer > 0 and int(self.animation_time * 12) % 2 == 0):
            name += "_flash"
        frames = art[name]
        frame = frames[int(time / FRAME_TIME) % len(frames)]
        if self.warning and self.attack_name == "RIFT AMBUSH":
            frame = self.rift_shadow
        screen.blit(frame, frame.get_rect(center=point))
        text = self.label(font, self.attack_name)
        screen.blit(text, text.get_rect(midtop=(point[0], point[1] + self.radius + 27)))
