import argparse
import math
import random
import pygame

import config
from arena import update_arena, draw_arena, draw_arena_warning
from boss import Boss, preload as preload_boss
from effects import Explosion, preload
from items import maybe_drop, update_items, draw_items
from menu import Menu
from player import Player
from projectiles import update_enemy_bullets, draw_enemy_bullets
from sounds import BossSounds, EnemyDeathSounds, PlayerDeathSound, DangerSounds
from warning import DangerDisplay
from yellow_enemy import YellowEnemy
from green_enemy import GreenEnemy
from red_enemy import RedEnemy
from ufo import UFO


def create_stars():
    stars = []
    for number in range(config.STAR_COUNT):
        depth = random.uniform(0.2, 0.8)
        brightness = int(80 + depth * 180)
        stars.append({
            "x": random.randrange(config.WIDTH),
            "y": random.randrange(config.HEIGHT),
            "depth": depth,
            "color": (brightness - 15, brightness - 5, brightness),
            "size": 2 if depth > 0.6 else 1,
        })
    return stars


def draw_stars(screen, stars, velocity, dt):
    for star in stars:
        # Nearby stars scroll faster. Wrapping keeps the number of stars fixed.
        star["x"] = (star["x"] - velocity.x * star["depth"] * dt) % config.WIDTH
        star["y"] = (star["y"] - velocity.y * star["depth"] * dt) % config.HEIGHT
        pygame.draw.circle(screen, star["color"], (int(star["x"]), int(star["y"])), star["size"])


def spawn_enemy(player, enemy_type):
    # Enemies arrive outside the view, never directly on top of the player.
    side = random.choice(("top", "bottom", "left", "right"))
    x = random.uniform(-config.WIDTH / 2, config.WIDTH / 2)
    y = random.uniform(-config.HEIGHT / 2, config.HEIGHT / 2)
    if side == "top":
        y = -config.HEIGHT / 2 - 80
    elif side == "bottom":
        y = config.HEIGHT / 2 + 80
    elif side == "left":
        x = -config.WIDTH / 2 - 80
    else:
        x = config.WIDTH / 2 + 80
    return enemy_type(player.position + pygame.Vector2(x, y))


def starting_enemies(player):
    return [spawn_enemy(player, kind) for kind in (YellowEnemy, GreenEnemy, RedEnemy, UFO)]


def difficulty_settings(score):
    tier = max(0, int(score)) // config.DIFFICULTY_SCORE_STEP
    # Every tier increases pressure, with gentle limits on speed and spawning.
    pressure = tier / (tier + 6)
    pace = config.ENEMY_START_PACE + (config.ENEMY_TOP_PACE - config.ENEMY_START_PACE) * pressure
    spawn_time = config.ENEMY_SPAWN_TIME - (config.ENEMY_SPAWN_TIME - config.MIN_ENEMY_SPAWN_TIME) * pressure
    enemy_limit = min(config.MAX_ENEMIES, config.BASE_ENEMY_LIMIT + tier * config.ENEMIES_PER_LEVEL)
    return tier, pace, spawn_time, enemy_limit


def spawn_wave(enemies, player, tier, enemy_limit):
    # Each level brings a larger group, without exceeding the on-screen limit.
    amount = min(config.MAX_SPAWN_AMOUNT, 1 + tier, max(0, enemy_limit - len(enemies)))
    choices = (YellowEnemy, YellowEnemy, YellowEnemy, YellowEnemy,
               GreenEnemy, GreenEnemy, RedEnemy, UFO)
    for number in range(amount):
        enemies.append(spawn_enemy(player, random.choice(choices)))


def shot_hit_time(start, end, center, radius):
    # Find the first point where a shot enters a circle: 0=start, 1=end.
    offset = start - center
    if offset.length_squared() <= radius * radius:
        return 0
    path = end - start
    length = path.length_squared()
    if length == 0:
        return None
    along = offset.dot(path)
    crossing = along * along - length * (offset.length_squared() - radius * radius)
    if crossing < 0:
        return None
    hit = (-along - math.sqrt(crossing)) / length
    return hit if 0 <= hit <= 1 else None


def shot_hits_circle(start, end, center, radius):
    return shot_hit_time(start, end, center, radius) is not None


def swept_hits_beam(start, end, beam_start, beam_end, radius):
    # Check the ends of both paths, including the laser's rounded tips.
    paths = ((start, end, beam_start), (start, end, beam_end),
             (beam_start, beam_end, start), (beam_start, beam_end, end))
    for path_start, path_end, center in paths:
        if shot_hits_circle(path_start, path_end, center, radius):
            return True

    # Fast movement can cross the middle even when all four ends are far away.
    movement = end - start
    beam = beam_end - beam_start
    crossing = movement.cross(beam)
    if abs(crossing) < 0.000001:
        return False
    offset = beam_start - start
    along_movement = offset.cross(beam) / crossing
    along_beam = offset.cross(movement) / crossing
    return 0 <= along_movement <= 1 and 0 <= along_beam <= 1


def update_enemies(enemies, bullets, player, dt, enemy_pace=1.0):
    if dt <= 0:
        return
    for enemy in enemies[:]:
        enemy.previous_position = enemy.position.copy()
        enemy.hit_timer = max(0, enemy.hit_timer - dt)
        if enemy.kind == "boss":
            # Boss warnings use real seconds, even at high difficulty.
            enemy.update(dt, player, bullets)
            if enemy.phase_changed:
                # Give the new phase a clean, readable opening.
                bullets.clear()
            continue
        enemy.animation_time += dt
        # Only hostile movement and attack timers speed up. UFOs stay bonuses.
        enemy.update(dt if enemy.bonus else dt * enemy_pace, player, bullets)
        distance = enemy.position.distance_squared_to(player.position)
        if enemy.escaped or distance > config.DESPAWN_DISTANCE ** 2:
            enemies.remove(enemy)

    update_enemy_bullets(bullets, player, dt)


def boss_beam_hits(player, boss):
    if not boss.beam_active and not boss.beam_was_active:
        return False
    first = boss.beam_active_start_fraction
    last = boss.beam_active_end_fraction
    if last <= first:
        return False
    player_start = player.previous_position.lerp(player.position, first)
    player_end = player.previous_position.lerp(player.position, last)
    radius = config.PLAYER_HIT_RADIUS + boss.beam_width / 2
    if not boss.beam_was_active:
        return swept_hits_beam(player_start, player_end,
                               boss.beam_start, boss.beam_end, radius)

    # Follow the moving beam between frames, including its final active frame.
    old_start, old_end = boss.beam_previous_start, boss.beam_previous_end
    motion = max(old_start.distance_to(boss.beam_start), old_end.distance_to(boss.beam_end))
    steps = max(1, math.ceil(motion / 12))
    margin = motion / (2 * steps)
    for index in range(steps):
        middle = (index + 0.5) / steps
        start = player_start.lerp(player_end, index / steps)
        end = player_start.lerp(player_end, (index + 1) / steps)
        beam_start = old_start.lerp(boss.beam_start, middle)
        beam_end = old_end.lerp(boss.beam_end, middle)
        if swept_hits_beam(start, end, beam_start, beam_end, radius + margin):
            return True
    return False


def check_collisions(player, enemies, bullets, explosions, items, enemy_sounds=None):
    points = 0
    zero = pygame.Vector2()
    for laser in player.lasers[:]:
        target = None
        first_hit = 2
        for enemy in enemies:
            # Relative movement also catches a fast enemy crossing a laser.
            first = getattr(enemy, "contact_start_fraction", 0)
            if first >= 1:
                continue
            start = laser["previous_position"].lerp(laser["position"], first) - enemy.previous_position
            start -= laser["direction"] * config.LASER_LENGTH
            end = laser["position"] - enemy.position
            hit = shot_hit_time(start, end, zero, enemy.radius + 2)
            if hit is not None:
                hit = first + (1 - first) * hit
            if hit is not None and hit < first_hit:
                target = enemy
                first_hit = hit
        if target is not None:
            player.lasers.remove(laser)
            if not getattr(target, "can_take_damage", True):
                continue
            target.health -= 1
            target.hit_timer = 0.12
            if target.health <= 0:
                enemies.remove(target)
                points += target.score
                explosions.append(Explosion(target.position, target.kind, target.color, target.score))
                if target.kind == "boss":
                    bullets.clear()
                    # The final hit ends combat before any more damage or points.
                    return points
                else:
                    if enemy_sounds is not None:
                        enemy_sounds.play()
                    maybe_drop(items, target.position)

    for bullet in bullets[:]:
        if bullet.get("mine"):
            continue
        first = bullet.get("active_start_fraction", 0)
        last = bullet.get("active_end_fraction", 0 if bullet.get("exploded") else 1)
        if last <= first:
            continue
        if bullet.get("trap"):
            start = player.previous_position.lerp(player.position, first)
            end = player.previous_position.lerp(player.position, last)
            if shot_hits_circle(start, end, bullet["position"], config.PLAYER_HIT_RADIUS + bullet["radius"]):
                player.take_damage(bullet["damage"])
            continue
        if bullet.get("motion_parts"):
            # A blade can turn around mid-frame; test both parts of its path.
            for part_start, part_end, part_first, part_last in bullet["motion_parts"]:
                start = part_start - player.previous_position.lerp(player.position, part_first)
                end = part_end - player.previous_position.lerp(player.position, part_last)
                if shot_hits_circle(start, end, zero, config.PLAYER_HIT_RADIUS + bullet.get("radius", 5)):
                    player.take_damage(bullet["damage"])
                    if bullet in bullets:
                        bullets.remove(bullet)
                    break
            continue
        if bullet.get("strike"):
            start = player.previous_position.lerp(player.position, first)
            end = player.previous_position.lerp(player.position, last)
            tip = bullet["position"] + bullet["direction"] * bullet["length"]
            if swept_hits_beam(start, end, bullet["position"], tip,
                               config.PLAYER_HIT_RADIUS + bullet["radius"]):
                player.take_damage(bullet["damage"])
            continue
        # A new shard cannot hit movement from before its parent exploded.
        start = bullet["previous_position"] - player.previous_position.lerp(player.position, first)
        end = bullet["position"] - player.previous_position.lerp(player.position, last)
        if shot_hits_circle(start, end, zero, config.PLAYER_HIT_RADIUS + bullet.get("radius", 5)):
            player.take_damage(bullet["damage"])
            bullets.remove(bullet)

    for enemy in enemies:
        if not enemy.bonus and getattr(enemy, "can_take_damage", True):
            if enemy.kind == "boss" and boss_beam_hits(player, enemy):
                player.take_damage(config.BOSS_LASER_DAMAGE)
            first = getattr(enemy, "contact_start_fraction", 0)
            if first >= 1:
                continue
            start = enemy.previous_position - player.previous_position.lerp(player.position, first)
            end = enemy.position - player.position
            if shot_hits_circle(start, end, zero, enemy.radius + config.PLAYER_HIT_RADIUS):
                player.take_damage(config.BOSS_CONTACT_DAMAGE if enemy.kind == "boss" else 1)
    return points


def update_explosions(explosions, dt):
    for explosion in explosions[:]:
        explosion.update(dt)
        if explosion.finished:
            explosions.remove(explosion)
    # Only the newest effects are needed if many enemies die together.
    if len(explosions) > config.MAX_EXPLOSIONS:
        del explosions[:-config.MAX_EXPLOSIONS]


def draw_enemies(screen, enemies, bullets, explosions, player, font, labels):
    offset = pygame.Vector2(screen.get_rect().center) - player.position
    view = screen.get_rect().inflate(140, 140)
    for enemy in enemies:
        if enemy.kind == "boss":
            enemy.draw(screen, player.position, font)
            continue
        center = enemy.position + offset
        if not view.collidepoint(center):
            continue
        frame = int(enemy.animation_time / config.FRAME_TIME) % len(enemy.frames)
        image = enemy.flash_frames[frame] if enemy.hit_timer > 0 else enemy.frames[frame]
        if enemy.warning:
            pygame.draw.circle(screen, enemy.color, center, enemy.radius + 9, 2)
            if enemy.kind == "yellow_enemy":
                tip = center + enemy.dash_direction * 150
                pygame.draw.line(screen, (110, 90, 35), center, tip, 1)
        screen.blit(image, image.get_rect(center=(round(center.x), round(center.y))))

        name = enemy.name
        if enemy.bonus:
            name += f"  {math.ceil(enemy.time_left)}s"
        if name not in labels:
            labels[name] = font.render(name, True, enemy.color)
        label = labels[name]
        bar = pygame.Rect(round(center.x) - 23, round(center.y) - enemy.radius - 9, 46, 4)
        screen.blit(label, label.get_rect(midbottom=(bar.centerx, bar.top - 4)))
        pygame.draw.rect(screen, (45, 55, 70), bar)
        bar.width = round(46 * enemy.health / enemy.max_health)
        pygame.draw.rect(screen, enemy.color, bar)

    draw_enemy_bullets(screen, bullets, offset)
    for explosion in explosions:
        explosion.draw(screen, player.position, font)


def draw_health_bar(screen, rectangle, health, max_health):
    # Green is healthy, yellow is hurt, and red means low health.
    rectangle = pygame.Rect(rectangle)
    maximum = max(1, int(max_health))
    amount = max(0, min(1, health / maximum))
    color = (85, 225, 135)
    if amount <= 0.3:
        color = (255, 85, 95)
    elif amount <= 0.6:
        color = (255, 205, 70)

    pygame.draw.rect(screen, (16, 28, 42), rectangle, border_radius=3)
    inside = rectangle.inflate(-4, -4)
    fill = inside.copy()
    fill.width = round(inside.width * amount)
    if fill.width > 0:
        pygame.draw.rect(screen, color, fill, border_radius=2)
    # Each section represents one health point.
    for point in range(1, maximum):
        x = inside.left + round(inside.width * point / maximum)
        pygame.draw.line(screen, (16, 28, 42), (x, inside.top), (x, inside.bottom - 1))
    pygame.draw.rect(screen, (85, 110, 130), rectangle, width=1, border_radius=3)


def draw_crosshair(screen, position, ready):
    x, y = position
    color = config.LASER_COLOR if ready else (120, 145, 165)
    pygame.draw.circle(screen, color, position, 7, 1)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        pygame.draw.line(screen, color, (x + dx * 10, y + dy * 10), (x + dx * 15, y + dy * 15))


def draw_boss_health(screen, boss, font, labels):
    phase = "ENRAGED" if boss.enraged else boss.phase_name
    text = f"{boss.name}    {phase}    {boss.attack_name}"
    if text not in labels:
        labels[text] = font.render(text, True, (255, 170, 95))
    label = labels[text]
    panel = pygame.Rect(screen.get_width() // 2 - 324, 82, 648, 54)
    pygame.draw.rect(screen, (10, 18, 30), panel, border_radius=6)
    screen.blit(label, label.get_rect(midtop=(screen.get_width() // 2, 88)))
    bar = pygame.Rect(screen.get_width() // 2 - 310, 114, 620, 15)
    pygame.draw.rect(screen, (40, 25, 36), bar, border_radius=4)
    fill = bar.inflate(-4, -4)
    fill.width = round(fill.width * max(0, boss.health) / boss.max_health)
    if fill.width > 0:
        pygame.draw.rect(screen, boss.color, fill, border_radius=2)
    pygame.draw.rect(screen, (190, 105, 95), bar, width=1, border_radius=4)
    for fraction in (1 / 3, 2 / 3):
        x = bar.left + round(bar.width * fraction)
        pygame.draw.line(screen, (40, 25, 36), (x, bar.top + 2), (x, bar.bottom - 3), 2)


def draw_boss_impact(screen, boss, world_image, arrival_flash):
    if boss is None or boss.health <= 0:
        return
    impact = boss.impact_timer / boss.impact_duration
    strength = max(impact, 0.18 if boss.beam_active else 0)
    if strength <= 0:
        return
    # Shake the picture briefly, keeping the HUD, mouse aim and physics steady.
    world_image.blit(screen, (0, 0))
    x = round(math.sin(boss.animation_time * 95) * 9 * strength)
    y = round(math.cos(boss.animation_time * 119) * 7 * strength)
    screen.fill(config.BACKGROUND_COLOR)
    screen.blit(world_image, (x, y))
    if impact > 0:
        arrival_flash.set_alpha(round(85 * impact ** 3))
        screen.blit(arrival_flash, (0, 0))


def draw_boss_direction(screen, boss, player, font, labels):
    if boss is None or boss.intro_timer > 0 or boss.health <= 0:
        return
    center = pygame.Vector2(screen.get_rect().center)
    difference = boss.position - player.position
    if screen.get_rect().inflate(160, 160).collidepoint(center + difference):
        return
    direction = difference.normalize()
    # Keep the arrow below the health bars and above the controls.
    alarm = boss.beam_active or boss.beam_warning or (boss.warning and boss.attack_name in ("ION STORM", "RIFT AMBUSH", "REAPER BLADES"))
    top = 240 if alarm else 160
    bounds = pygame.Rect(30, top, screen.get_width() - 60, screen.get_height() - top - 70)
    horizontal = (bounds.right - center.x) if direction.x >= 0 else (center.x - bounds.left)
    vertical = (bounds.bottom - center.y) if direction.y >= 0 else (center.y - bounds.top)
    scale = min(horizontal / max(abs(direction.x), 0.0001),
                vertical / max(abs(direction.y), 0.0001))
    tip = center + direction * scale
    side = direction.rotate(90) * 9
    base = tip - direction * 20
    color = (255, 100, 120) if boss.beam_active or boss.beam_warning else boss.color
    pygame.draw.polygon(screen, color, (tip, base + side, base - side))
    text = "DEATHRAY" if boss.beam_active or boss.beam_warning else "BOSS"
    key = ("direction", text)
    if key not in labels:
        labels[key] = font.render(text, True, (255, 170, 110))
    label = labels[key]
    rectangle = label.get_rect(center=tip - direction * 50)
    rectangle.clamp_ip(bounds)
    screen.blit(label, rectangle)


def main(boss_health=None):
    pygame.init()
    screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
    title = config.TITLE
    if boss_health is not None:
        title += f" - Boss Test ({boss_health} HP)"
    pygame.display.set_caption(title)
    preload()
    preload_boss()
    boss_sounds = BossSounds()
    enemy_sounds = EnemyDeathSounds()
    player_death_sound = PlayerDeathSound()
    danger_sounds = DangerSounds()
    player = Player()
    pygame.display.set_icon(player.idle_image)
    menu = Menu(screen.get_size())
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 26)
    small_font = pygame.font.Font(None, 22)
    title_font = pygame.font.Font(None, 52)
    danger_display = DangerDisplay(screen.get_size())

    controls = small_font.render("WASD  Move    Mouse  Aim    Left click  Shoot    Hold Space  Nitro    P  Pause    Esc  Quit", True, (175, 195, 210))
    pause_title = title_font.render("PAUSED", True, config.TEXT_COLOR)
    pause_hint = font.render("P to resume", True, config.TEXT_COLOR)
    health_label = small_font.render("HEALTH", True, config.TEXT_COLOR)
    boss_warning = title_font.render("BOSS INCOMING", True, (255, 160, 95))
    goal_text = f"FINAL BOSS AT {config.BOSS_SCORE_TARGET:,}"
    if boss_health is not None:
        goal_text = f"BOSS TEST - {boss_health} HP"
    boss_goal = small_font.render(goal_text, True, (255, 170, 95))
    completed_label = small_font.render("MISSION COMPLETE", True, (115, 245, 185))
    winning_title = title_font.render(f"BOSS DEFEATED   +{config.BOSS_SCORE:,}", True, (115, 245, 185))
    dimmer = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    dimmer.fill((3, 7, 15, 190))
    damage_flash = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    damage_flash.fill((180, 30, 45, 45))
    world_image = pygame.Surface(screen.get_size()).convert()
    arrival_flash = pygame.Surface(screen.get_size()).convert()
    arrival_flash.fill((220, 245, 255))
    hud_panel = pygame.Surface((config.WIDTH, 78), pygame.SRCALPHA)
    hud_panel.fill((5, 9, 19, 235))
    controls_panel = pygame.Surface((config.WIDTH, 42), pygame.SRCALPHA)
    controls_panel.fill((5, 9, 19, 235))
    labels = {}
    last_status = None
    status_image = None
    last_difficulty = None
    difficulty_image = None
    difficulty_notice = 0
    notice_image = None

    stars = create_stars()
    enemies = []
    enemy_bullets = []
    explosions = []
    items = []
    state = "menu"
    score = 0
    best_score = 0
    survival_time = 0
    death_time = 0
    boss = None
    tier, enemy_pace, spawn_interval, enemy_limit = difficulty_settings(score)
    spawn_timer = spawn_interval
    running = True
    paused = False
    focused = True
    mouse_ready = False
    auto_start = boss_health is not None

    while running:
        resting = state not in ("playing", "winning") or paused or not focused
        dt = min(clock.tick(30 if resting else config.FPS) / 1000, 0.05)
        clicked = False
        start_requested = auto_start
        auto_start = False
        menu_requested = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state == "menu":
                    if menu.start_button.collidepoint(event.pos):
                        start_requested = True
                    elif menu.quit_button.collidepoint(event.pos):
                        running = False
                elif state in ("game_over", "victory"):
                    if menu.again_button.collidepoint(event.pos):
                        start_requested = True
                    elif menu.menu_button.collidepoint(event.pos):
                        menu_requested = True
                elif state == "playing":
                    clicked = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_RETURN and state in ("menu", "game_over", "victory"):
                    start_requested = True
                elif event.key == pygame.K_m and state in ("game_over", "victory"):
                    menu_requested = True
                elif event.key == pygame.K_p and state in ("playing", "winning") and player.health > 0:
                    paused = not paused
            elif event.type == pygame.WINDOWFOCUSLOST:
                focused = False
            elif event.type == pygame.WINDOWFOCUSGAINED:
                focused = True
        if not running:
            break

        if menu_requested:
            boss_sounds.stop()
            enemy_sounds.stop()
            player_death_sound.stop()
            danger_sounds.stop()
            state = "menu"
            enemies.clear()
            enemy_bullets.clear()
            explosions.clear()
            items.clear()
            boss = None
            player.reset()
            paused = False
            start_requested = False
        if start_requested:
            boss_sounds.stop()
            enemy_sounds.stop()
            player_death_sound.stop()
            danger_sounds.stop()
            player.reset()
            enemies = starting_enemies(player) if boss_health is None else []
            enemy_bullets.clear()
            explosions.clear()
            items.clear()
            score = 0 if boss_health is None else config.BOSS_SCORE_TARGET
            survival_time = 0
            death_time = 0
            tier, enemy_pace, spawn_interval, enemy_limit = difficulty_settings(score)
            spawn_timer = spawn_interval
            difficulty_notice = 0
            boss = None
            if boss_health is not None:
                boss = Boss(player.position + pygame.Vector2(0, -config.BOSS_ENTRY_DISTANCE))
                boss.health = max(1, min(boss.max_health, int(boss_health)))
                enemies.append(boss)
                boss_sounds.start()
            state = "playing"
            paused = False
            clicked = False
            mouse_ready = False

        mouse_position = pygame.mouse.get_pos()
        held = pygame.mouse.get_pressed()[0]
        if not held:
            mouse_ready = True
        if paused or not focused:
            dt = 0
        if state == "playing":
            if dt > 0 and player.health > 0:
                difficulty_notice = max(0, difficulty_notice - dt)
                survival_time += dt
                keys = pygame.key.get_pressed()
                shooting = mouse_ready and (clicked or held)
                player.update(keys, dt, mouse_position, shooting)
                update_enemies(enemies, enemy_bullets, player, dt, enemy_pace)
                score += check_collisions(player, enemies, enemy_bullets, explosions, items, enemy_sounds)
                if boss is not None and boss not in enemies:
                    boss_sounds.defeated()
                    boss = None
                    state = "winning"
                    enemies.clear()
                    enemy_bullets.clear()
                    items.clear()
                    player.lasers.clear()
                    player.velocity.update(0, 0)
                    player.thrusting = False
                    player.hit_timer = 0
                    player.rapid_fire_timer = 0
                    player.stop_nitro()
                    difficulty_notice = 0
                else:
                    if boss is not None:
                        update_arena(boss, player, dt)
                    if player.health > 0:
                        score += update_items(items, player, dt)
                best_score = max(best_score, score)
                if state == "playing":
                    new_tier, enemy_pace, spawn_interval, enemy_limit = difficulty_settings(score)
                    if new_tier > tier:
                        difficulty_notice = 2.0
                        text = f"DIFFICULTY {new_tier + 1} - UP TO {enemy_limit} ENEMIES, LARGER WAVES"
                        notice_image = font.render(text, True, (255, 200, 105))
                        spawn_timer = min(spawn_timer, spawn_interval)
                    tier = new_tier
                    if player.health > 0 and boss is None:
                        if score >= config.BOSS_SCORE_TARGET:
                            # Make room for the final boss entrance and solo fight.
                            enemies.clear()
                            enemy_bullets.clear()
                            player.lasers.clear()
                            items.clear()
                            boss = Boss(player.position + pygame.Vector2(0, -config.BOSS_ENTRY_DISTANCE))
                            enemies.append(boss)
                            boss_sounds.start()
                            difficulty_notice = 0
                        else:
                            spawn_timer -= dt
                            if spawn_timer <= 0:
                                spawn_wave(enemies, player, tier, enemy_limit)
                                spawn_timer = spawn_interval

            if player.health == 0 and not player.death_effect_played:
                player.death_effect_played = True
                player_death_sound.play()
                player.velocity.update(0, 0)
                player.lasers.clear()
                player.stop_nitro()
                explosions.append(Explosion(player.position, "player", (255, 165, 75)))
        if state in ("playing", "winning"):
            update_explosions(explosions, dt)
            if state == "winning" and not any(effect.kind == "boss" for effect in explosions):
                state = "victory"
            elif state == "playing" and player.health == 0:
                death_time += dt
                if death_time >= 0.9:
                    state = "game_over"

        if state not in ("playing", "winning", "victory") or player.health <= 0:
            boss_sounds.stop()
        else:
            boss_sounds.set_paused(paused or not focused)
            boss_sounds.update(boss, dt)
        if state != "playing" or player.health <= 0:
            enemy_sounds.stop()
        else:
            enemy_sounds.set_paused(paused or not focused)
        # Let the player's death sound finish while the final-score screen is open.
        player_death_sound.set_paused(paused or not focused)
        if state == "playing" and player.health > 0:
            danger_sounds.set_paused(paused or not focused)
            danger_sounds.update(boss, player, dt)
        else:
            danger_sounds.stop()

        screen.fill(config.BACKGROUND_COLOR)
        background_velocity = pygame.Vector2(12, 5) if state == "menu" else player.velocity
        draw_stars(screen, stars, background_velocity, dt if player.health > 0 else 0)
        if state == "menu":
            menu.draw_start(screen, mouse_position, best_score)
        else:
            if player.health > 0:
                draw_arena(screen, boss, player)
                danger_display.draw_world(screen, boss, player)
            draw_items(screen, items, player.position, small_font)
            draw_enemies(screen, enemies, enemy_bullets, explosions, player, small_font, labels)
            player.draw(screen)
            if player.health > 0:
                center = screen.get_rect().center
                draw_health_bar(screen, (center[0] - 39, center[1] + 92, 78, 9), player.health, config.PLAYER_HEALTH)
            if player.health > 0 and player.hit_timer > config.PLAYER_HIT_COOLDOWN - 0.12:
                screen.blit(damage_flash, (0, 0))
            if player.health > 0:
                draw_boss_impact(screen, boss, world_image, arrival_flash)
                draw_boss_direction(screen, boss, player, small_font, labels)

            # Keep the HUD readable when larger waves fly behind it.
            screen.blit(hud_panel, (0, 0))
            screen.blit(controls_panel, (0, config.HEIGHT - 42))
            rapid = math.ceil(player.rapid_fire_timer)
            status = (score, best_score, player.health, int(player.velocity.length()), int(survival_time), rapid)
            if status != last_status:
                text = f"SCORE {score:,}    BEST {best_score:,}    HEALTH {player.health}/{config.PLAYER_HEALTH}    SPEED {status[3]}    TIME {status[4]}s"
                if rapid > 0:
                    text += f"    RAPID FIRE {rapid}s"
                status_image = font.render(text, True, config.TEXT_COLOR)
                last_status = status
            screen.blit(status_image, (20, 20))
            screen.blit(health_label, (20, 52))
            draw_health_bar(screen, (95, 53, 190, 16), player.health, config.PLAYER_HEALTH)
            completed = state in ("winning", "victory")
            difficulty_key = (tier, len(enemies), enemy_limit, completed)
            if difficulty_key != last_difficulty:
                if completed:
                    text = f"DIFFICULTY {tier + 1}    BOSS DEFEATED"
                else:
                    next_score = (tier + 1) * config.DIFFICULTY_SCORE_STEP
                    text = f"DIFFICULTY {tier + 1}    ENEMIES {len(enemies)}/{enemy_limit}    NEXT {next_score:,}"
                difficulty_image = small_font.render(text, True, (180, 205, 220))
                last_difficulty = difficulty_key
            screen.blit(difficulty_image, (310, 53))
            if not completed and player.health > 0:
                fuel = round(player.nitro_fuel)
                text = f"NITRO {fuel}%"
                if player.nitro_locked:
                    text = "RELEASE SPACE" if player.nitro_fuel >= config.PLAYER_NITRO_RESTART_FUEL else "NITRO RECHARGING"
                key = (text, player.nitro_active)
                if key not in labels:
                    labels[key] = small_font.render(text, True, (255, 190, 85) if player.nitro_active else (90, 225, 255))
                screen.blit(labels[key], (780, 51))
                pygame.draw.rect(screen, (25, 45, 60), (780, 70, 145, 3))
                charge = player.nitro_fuel / 100
                pygame.draw.rect(screen, (75, 210, 245), (780, 70, round(145 * charge), 3))
                capacity = 780 + round(145 * config.PLAYER_NITRO_FUEL / 100)
                pygame.draw.line(screen, (180, 200, 215), (capacity, 68), (capacity, 74))
            goal_image = completed_label if state in ("winning", "victory") else boss_goal
            screen.blit(goal_image, goal_image.get_rect(topright=(config.WIDTH - 20, 53)))
            # Reveal the fight bar after the entrance so the descent stays visible.
            if boss is not None and boss.intro_timer == 0:
                draw_boss_health(screen, boss, small_font, labels)
            elif boss is not None and boss.intro_duration - boss.intro_timer < boss.approach_time:
                screen.blit(boss_warning, boss_warning.get_rect(midtop=(config.WIDTH // 2, 150)))
            if player.health > 0:
                danger_display.draw_hud(screen, boss, player)
                draw_arena_warning(screen, boss, player, small_font, labels)
            if state == "winning":
                screen.blit(winning_title, winning_title.get_rect(midtop=(screen.get_width() // 2, 145)))
            elif difficulty_notice > 0 and player.health > 0 and boss is None:
                screen.blit(notice_image, notice_image.get_rect(midtop=(screen.get_width() // 2, 88)))
            if not completed:
                screen.blit(controls, (20, config.HEIGHT - 32))

            if state == "game_over":
                screen.blit(dimmer, (0, 0))
                menu.draw_game_over(screen, mouse_position, score, best_score, survival_time)
            elif state == "victory":
                screen.blit(dimmer, (0, 0))
                menu.draw_victory(screen, mouse_position, score, best_score, survival_time)
            elif paused or not focused:
                screen.blit(dimmer, (0, 0))
                panel = pygame.Rect(0, 0, 570, 170)
                panel.center = screen.get_rect().center
                pygame.draw.rect(screen, (9, 17, 29), panel, border_radius=12)
                pygame.draw.rect(screen, (40, 60, 80), panel, width=1, border_radius=12)
                center = screen.get_rect().center
                screen.blit(pause_title, pause_title.get_rect(center=(center[0], center[1] - 25)))
                screen.blit(pause_hint, pause_hint.get_rect(center=(center[0], center[1] + 28)))
            if state == "playing" and player.health > 0 and focused and not paused:
                draw_crosshair(screen, mouse_position, player.shoot_timer == 0)

        pygame.mouse.set_visible(state != "playing" or paused or not focused or player.health <= 0)
        pygame.display.flip()

    pygame.mouse.set_visible(True)
    boss_sounds.stop()
    enemy_sounds.stop()
    player_death_sound.stop()
    danger_sounds.stop()
    pygame.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Play Void Gazer.")
    parser.add_argument("--boss-health", choices=("full", "1"),
                        help="Start a boss test at full health or 1 health.")
    arguments = parser.parse_args()
    health = None
    if arguments.boss_health == "full":
        health = config.BOSS_HEALTH
    elif arguments.boss_health == "1":
        health = 1
    main(boss_health=health)
