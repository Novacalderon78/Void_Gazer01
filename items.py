import math
import random

import pygame

import config


ITEM_COLORS = {"health": (90, 235, 135), "rapid": (70, 220, 255), "points": (255, 205, 80)}
label_images = {}


def maybe_drop(items, position):
    # A defeated enemy sometimes leaves one item behind.
    if len(items) >= config.MAX_ITEMS or random.random() >= config.ITEM_DROP_CHANCE:
        return None
    item = {
        "position": pygame.Vector2(position),
        "kind": random.choice(("health", "rapid", "points")),
        "time_left": config.ITEM_LIFETIME,
        "age": 0,
    }
    items.append(item)
    return item


def update_items(items, player, dt):
    if dt <= 0:
        return 0
    bonus_points = 0
    for item in items[:]:
        item["age"] += dt
        item["time_left"] -= dt
        distance = item["position"].distance_to(player.position)
        if item["time_left"] <= 0 or distance > config.DESPAWN_DISTANCE:
            items.remove(item)
            continue
        if player.health <= 0 or distance > config.ITEM_PICKUP_RADIUS:
            continue

        if item["kind"] == "health":
            # Save health items on the ground until the player needs them.
            if player.health >= config.PLAYER_HEALTH:
                continue
            player.health = min(config.PLAYER_HEALTH, player.health + 1)
        elif item["kind"] == "rapid":
            player.rapid_fire_timer = config.RAPID_FIRE_DURATION
            player.shoot_timer = min(player.shoot_timer, config.LASER_COOLDOWN * 0.5)
        elif item["kind"] == "points":
            bonus_points += config.ITEM_BONUS_POINTS
        items.remove(item)
    return bonus_points


def draw_items(screen, items, player_position, font):
    # Render each label once, then reuse it every frame.
    if font not in label_images:
        names = {"health": "+1 HP", "rapid": "RAPID", "points": "+" + str(config.ITEM_BONUS_POINTS)}
        label_images[font] = {
            kind: font.render(name, True, ITEM_COLORS[kind])
            for kind, name in names.items()
        }

    center = pygame.Vector2(screen.get_rect().center)
    for item in items:
        position = item["position"] - player_position + center
        # Do not draw items outside the window, or during a warning blink.
        if not screen.get_rect().inflate(120, 120).collidepoint(position):
            continue
        if item["time_left"] < 3 and int(item["time_left"] * 6) % 2 == 0:
            continue

        position.y += math.sin(item["age"] * 4) * 4
        x, y = round(position.x), round(position.y)
        color = ITEM_COLORS[item["kind"]]
        radius = 20 + round(math.sin(item["age"] * 4))
        pygame.draw.circle(screen, (12, 25, 39), (x, y), radius)
        pygame.draw.circle(screen, color, (x, y), radius, 2)

        if item["kind"] == "health":
            pygame.draw.rect(screen, color, (x - 3, y - 11, 6, 22), border_radius=1)
            pygame.draw.rect(screen, color, (x - 11, y - 3, 22, 6), border_radius=1)
        elif item["kind"] == "rapid":
            bolt = [(x + 3, y - 13), (x - 9, y + 2), (x - 1, y + 2),
                    (x - 4, y + 13), (x + 10, y - 3), (x + 2, y - 3)]
            pygame.draw.polygon(screen, color, bolt)
        else:
            diamond = [(x, y - 12), (x + 10, y), (x, y + 12), (x - 10, y)]
            pygame.draw.polygon(screen, color, diamond)
            pygame.draw.line(screen, (255, 245, 210), (x, y - 7), (x + 5, y), 2)

        label = label_images[font][item["kind"]]
        screen.blit(label, label.get_rect(midtop=(x, y + 26)))
