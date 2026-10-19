import math

import pygame


def update_arena(boss, player, dt):
    if dt <= 0 or boss is None or boss.health <= 0 or player.health <= 0:
        return

    # Follow the entrance, then keep this arena fixed for the whole fight.
    if boss.intro_timer > 0:
        boss.arena_center = player.position.copy()
        boss.arena_ready = False
        return
    if not getattr(boss, "arena_ready", False):
        boss.arena_center = player.position.copy()
        boss.arena_ready = True
        boss.arena_outside_time = 0

    target_radius = (720, 660, 600)[boss.phase - 1]
    change = max(-60 * dt, min(60 * dt, target_radius - boss.arena_radius))
    boss.arena_radius += change

    # Phase changes and teleport warnings give the player a protected break.
    if not boss.can_take_damage:
        boss.arena_outside_time = 0
        return
    if player.position.distance_squared_to(boss.arena_center) <= boss.arena_radius ** 2:
        boss.arena_outside_time = 0
        return

    boss.arena_outside_time += dt
    if boss.arena_outside_time + 0.000000001 >= 0.85:
        # Normal hit protection limits repeated storm damage to once per second.
        player.take_damage(1)


def draw_arena(screen, boss, player):
    if boss is None or boss.health <= 0 or boss.intro_timer > 0:
        return
    if not getattr(boss, "arena_ready", False):
        return

    center = boss.arena_center - player.position + pygame.Vector2(screen.get_rect().center)
    radius = boss.arena_radius
    distance = player.position.distance_to(boss.arena_center)
    color = ((60, 205, 200), (235, 175, 70), (245, 105, 75))[boss.phase - 1]
    if distance > radius - 90:
        pulse = (math.sin(boss.animation_time * 8) + 1) / 2
        if distance > radius:
            color = (255, round(85 + pulse * 55), 70)
        else:
            color = tuple(round(value * (0.7 + pulse * 0.3)) for value in color)

    # Vector rings and inward arrows need no extra full-screen image each frame.
    rect = pygame.Rect(round(center.x - radius), round(center.y - radius),
                       round(radius * 2), round(radius * 2))
    pygame.draw.circle(screen, (22, 47, 59), center, round(radius + 9), 2)
    pygame.draw.circle(screen, (25, 62, 68), center, round(radius - 9), 1)
    for segment in range(48):
        angle = segment * math.tau / 48
        pygame.draw.arc(screen, color, rect, angle, angle + math.tau / 48 * 0.75, 3)
    for angle in range(0, 360, 30):
        outward = pygame.Vector2(1, 0).rotate(angle)
        sideways = outward.rotate(90) * 9
        base = center + outward * (radius + 3)
        tip = center + outward * (radius - 18)
        pygame.draw.lines(screen, color, False, (base - sideways, tip, base + sideways), 2)


def draw_arena_warning(screen, boss, player, font, labels):
    if boss is None or boss.health <= 0 or player.health <= 0 or boss.intro_timer > 0:
        return
    if not getattr(boss, "arena_ready", False) or not boss.can_take_damage:
        return
    if player.position.distance_squared_to(boss.arena_center) <= boss.arena_radius ** 2:
        return

    title = "MOVE BACK INSIDE THE ARENA"
    if boss.arena_outside_time + 0.000000001 < 0.85:
        seconds = math.ceil(max(0, 0.85 - boss.arena_outside_time) * 10) / 10
        detail = f"STORM DAMAGE IN {seconds:.1f}"
    else:
        detail = "VOID STORM - HULL DAMAGE"

    images = []
    for text, color in ((title, (255, 205, 160)), (detail, (255, 125, 105))):
        key = ("arena", id(font), text, color)
        if key not in labels:
            labels[key] = font.render(text, True, color)
        images.append(labels[key])

    width = max(image.get_width() for image in images) + 36
    panel = pygame.Rect((screen.get_width() - width) // 2, screen.get_height() - 116, width, 61)
    pygame.draw.rect(screen, (32, 15, 22), panel, border_radius=5)
    pygame.draw.rect(screen, (235, 100, 75), panel, 2, border_radius=5)
    screen.blit(images[0], images[0].get_rect(midtop=(panel.centerx, panel.y + 8)))
    screen.blit(images[1], images[1].get_rect(midtop=(panel.centerx, panel.y + 33)))
