import math
import pygame
import config


trap_images = {}


def make_shards(shot, count, speed, room, extra_time, frame_time):
    shards = []
    for index in range(min(count, max(0, room))):
        velocity = pygame.Vector2(speed, 0).rotate(index * 360 / count)
        position = shot["position"].copy()
        shards.append({
            "previous_position": position.copy(),
            "position": position + velocity * extra_time,
            "velocity": velocity,
            "time_left": 2.4 - extra_time,
            "color": shot["color"],
            "damage": 1,
            "radius": 5,
            "boss": True,
            "active_start_fraction": max(0, 1 - extra_time / frame_time),
        })
    return shards


def move_blade(shot, dt, delay, step):
    # Keep both straight paths when a blade reverses during this frame.
    elapsed = delay
    if not shot.get("returning"):
        travel = min(step, max(0, shot["return_timer"]))
        start = shot["position"].copy()
        shot["position"] += shot["velocity"] * travel
        if travel > 0:
            shot["motion_parts"].append((start, shot["position"].copy(), min(1, elapsed / dt), min(1, (elapsed + travel) / dt)))
        shot["return_timer"] = max(0, shot["return_timer"] - travel)
        if shot["return_timer"] < 0.000000001:
            shot["return_timer"] = 0
        elapsed += travel
        step -= travel
        if shot["return_timer"] == 0:
            shot["returning"] = True

    if shot.get("returning"):
        difference = shot["return_target"] - shot["position"]
        distance = difference.length()
        speed = shot.get("return_speed", 520)
        travel = min(step, distance / speed)
        start = shot["position"].copy()
        if distance > 0:
            shot["velocity"] = difference / distance * speed
            shot["position"] += shot["velocity"] * travel
        if travel > 0:
            shot["motion_parts"].append((start, shot["position"].copy(), min(1, elapsed / dt), min(1, (elapsed + travel) / dt)))
        if distance <= speed * step + 0.000001:
            shot["position"] = shot["return_target"].copy()
            shot["velocity"] = pygame.Vector2()
            shot["exploded"] = True
            shot["time_left"] = max(0, 0.25 - (step - travel))
            shot["active_end_fraction"] = min(1, (elapsed + travel) / dt)


def update_enemy_bullets(bullets, player, dt):
    if dt <= 0:
        return
    remaining = []
    new_shots = []
    boss_count = sum(shot.get("boss", False) for shot in bullets)
    for shot in bullets:
        shot["previous_position"] = shot["position"].copy()
        if shot.get("blade"):
            shot["motion_parts"] = []
        shot["active_start_fraction"] = 0
        shot["active_end_fraction"] = 0 if shot.get("exploded") else 1
        delay = max(0, min(dt, shot.pop("spawn_delay", 0)))
        step = dt - delay
        shot["active_start_fraction"] = delay / dt
        alive_time = min(step, max(0, shot["time_left"]))
        shot["time_left"] -= step
        if shot.get("trap"):
            wait = min(step, max(0, shot["arm_timer"]))
            shot["arm_timer"] = max(0, shot["arm_timer"] - wait)
            if shot["arm_timer"] < 0.000000001:
                shot["arm_timer"] = 0
            burning = min(step - wait, max(0, shot["blast_timer"]))
            shot["blast_timer"] = max(0, shot["blast_timer"] - burning)
            shot["active_start_fraction"] = min(1, (delay + wait) / dt)
            shot["active_end_fraction"] = min(1, (delay + wait + burning) / dt)
            if burning > 0:
                shot["detonated"] = True
        elif shot.get("blade") and not shot.get("exploded"):
            move_blade(shot, dt, delay, step)
        elif shot.get("strike"):
            shot["active_start_fraction"] = delay / dt
            shot["active_end_fraction"] = (delay + alive_time) / dt
        elif shot.get("mine"):
            if not shot.get("exploded"):
                shot["fuse"] -= step
                if shot["fuse"] <= 0:
                    # The marker itself is harmless. Only its flying shards hurt.
                    shot["exploded"] = True
                    shot["time_left"] = 0.25
                    count = shot.get("burst_count", 8)
                    shards = make_shards(shot, count, shot.get("burst_speed", 300),
                                         config.BOSS_BULLET_LIMIT - boss_count,
                                         min(step, -shot["fuse"]), dt)
                    new_shots.extend(shards)
                    boss_count += len(shards)
        elif shot.get("meteor") and not shot.get("exploded"):
            travel_time = min(step, max(0, shot["split_timer"]))
            shot["position"] += shot["velocity"] * travel_time
            shot["split_timer"] -= step
            if shot["split_timer"] <= 0:
                shards = make_shards(shot, shot.get("split_count", 6),
                                     shot.get("split_speed", 300),
                                     config.BOSS_BULLET_LIMIT - boss_count,
                                     min(step, -shot["split_timer"]), dt)
                new_shots.extend(shards)
                boss_count += len(shards)
                # Keep the burst briefly visible without a second contact hit.
                shot["exploded"] = True
                shot["time_left"] = 0.25
                shot["velocity"] = pygame.Vector2()
                shot["active_end_fraction"] = (delay + travel_time) / dt
        else:
            velocity = shot["velocity"]
            tracking = shot.get("homing_timer", 0)
            if tracking > 0 and velocity.length_squared() > 0:
                target = player.position - shot["position"]
                if target.length_squared() > 0:
                    turn = shot.get("turn_speed", 65) * min(step, tracking)
                    angle = velocity.angle_to(target)
                    angle = (angle + 180) % 360 - 180
                    shot["velocity"] = velocity.rotate(max(-turn, min(turn, angle)))
                shot["homing_timer"] = max(0, tracking - step)
            shot["position"] += (velocity + shot["velocity"]) * (step / 2)
        distance = shot["position"].distance_squared_to(player.position)
        # Keep a strike's final partial frame so collision still sees that time.
        visible = shot["time_left"] > 0 or (shot.get("strike") and alive_time > 0)
        if visible and distance <= config.DESPAWN_DISTANCE ** 2:
            remaining.append(shot)
    bullets[:] = (remaining + new_shots)[-config.MAX_ENEMY_BULLETS:]


def draw_enemy_bullets(screen, bullets, offset):
    view = screen.get_rect().inflate(180, 180)
    for shot in bullets:
        center = shot["position"] + offset
        if shot.get("strike"):
            if shot["time_left"] > 0:
                end = center + shot["direction"] * shot["length"]
                pygame.draw.line(screen, (115, 65, 220), center, end, round(shot["radius"] * 2))
                pygame.draw.line(screen, (220, 180, 255), center, end, 16)
                pygame.draw.line(screen, (255, 250, 255), center, end, 5)
            continue
        if not view.collidepoint(center):
            continue
        color = shot["color"]
        radius = shot.get("radius", 5)
        if shot.get("trap"):
            if not shot.get("detonated"):
                progress = max(0, min(1, 1 - shot["arm_timer"] / 0.85))
                pygame.draw.circle(screen, (135, 60, 35), center, radius, 1)
                pygame.draw.circle(screen, color, center, round(radius + 20 * (1 - progress)), 2)
                bounds = pygame.Rect(0, 0, radius * 2, radius * 2)
                bounds.center = center
                pygame.draw.arc(screen, color, bounds, -math.pi / 2,
                                -math.pi / 2 + max(0.01, progress * math.tau), 4)
                pygame.draw.line(screen, color, center + (-12, -12), center + (12, 12), 3)
                pygame.draw.line(screen, color, center + (-12, 12), center + (12, -12), 3)
            elif shot["blast_timer"] > 0:
                key = (radius, color)
                if key not in trap_images:
                    size = round(radius * 2 + 8)
                    glow = pygame.Surface((size, size), pygame.SRCALPHA)
                    point = glow.get_rect().center
                    pygame.draw.circle(glow, (*color, 145), point, radius)
                    pygame.draw.circle(glow, (255, 220, 160, 230), point, radius, 4)
                    pygame.draw.circle(glow, (255, 240, 200, 220), point, round(radius * 0.55), 2)
                    trap_images[key] = glow
                image = trap_images[key]
                screen.blit(image, image.get_rect(center=(round(center.x), round(center.y))))
            else:
                pygame.draw.circle(screen, (150, 60, 40), center, radius + 5, 2)
            continue
        if shot.get("exploded"):
            progress = max(0, min(1, 1 - shot["time_left"] / 0.25))
            pygame.draw.circle(screen, color, center, round(20 + progress * 65), 2)
            continue
        if shot.get("mine"):
            progress = max(0, min(1, 1 - shot["fuse"] / 1.2))
            pygame.draw.circle(screen, (95, 45, 95), center, 35, 1)
            marker = pygame.Rect(0, 0, 70, 70)
            marker.center = center
            pygame.draw.arc(screen, color, marker, -math.pi / 2,
                            -math.pi / 2 + max(0.01, progress * math.tau), 3)
            points = [center + pygame.Vector2(0, -radius).rotate(angle)
                      for angle in (0, 90, 180, 270)]
            pygame.draw.polygon(screen, color, points, 2)
            pygame.draw.circle(screen, (255, 240, 255), center, 3)
        else:
            if shot.get("blade"):
                angle = (2.4 - shot["time_left"]) * 720
                pygame.draw.circle(screen, color, center, radius + 4, 2)
                for turn in (0, 90, 180, 270):
                    arm = pygame.Vector2(radius + 5, 0).rotate(angle + turn)
                    pygame.draw.line(screen, (255, 220, 240), center + arm * 0.35,
                                     center + arm, 3)
            if shot.get("meteor"):
                tail = center - pygame.Vector2(0, 46)
                pygame.draw.line(screen, (130, 65, 30), tail, center, 12)
                pygame.draw.line(screen, (255, 150, 65), tail + (0, 12), center, 5)
                pygame.draw.circle(screen, (255, 190, 90), center, radius + 3, 1)
            if shot.get("homing_timer", 0) > 0:
                velocity = shot["velocity"]
                if velocity.length_squared() > 0:
                    tail = center - velocity.normalize() * 22
                    pygame.draw.line(screen, (100, 95, 60), tail, center, 4)
                pygame.draw.circle(screen, color, center, radius + 4, 1)
            pygame.draw.circle(screen, color, center, radius)
            pygame.draw.circle(screen, (255, 245, 230), center, 2)
