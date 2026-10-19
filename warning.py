import math
import pygame


class DangerDisplay:
    def __init__(self, size):
        self.layer = pygame.Surface(size, pygame.SRCALPHA)
        self.width, self.height = size
        self.title_font = pygame.font.Font(None, 34)
        self.hint_font = pygame.font.Font(None, 23)
        self.timer_font = pygame.font.Font(None, 48)
        self.labels = {}

    def label(self, text, font, color):
        key = (text, id(font), color)
        if key not in self.labels:
            self.labels[key] = font.render(text, True, color)
        return self.labels[key]

    def draw_world(self, screen, boss, player):
        if boss is None or not boss.beam_warning:
            return
        self.layer.fill((0, 0, 0, 0))
        center = boss.position - player.position + pygame.Vector2(self.width / 2, self.height / 2)
        progress = 1 - boss.timer / boss.beam_warning_duration
        pulse = (math.sin(boss.animation_time * 7) + 1) / 2
        radius = boss.beam_length + boss.radius + 6
        # Color the entire half-circle that the beam will sweep through.
        points = [center]
        for angle in range(-90, 91, 3):
            direction = boss.beam_center_direction.rotate(angle * boss.beam_sweep_sign)
            points.append(center + direction * radius)
        pygame.draw.polygon(self.layer, (230, 30, 65, round(32 + 12 * pulse + 16 * progress)), points)
        for angle in (-90, 90):
            direction = boss.beam_center_direction.rotate(angle * boss.beam_sweep_sign)
            end = center + direction * radius
            pygame.draw.line(self.layer, (255, 90, 105, 200), center, end, 4)
            safe = boss.beam_center_direction.rotate((angle + (-6 if angle < 0 else 6)) * boss.beam_sweep_sign)
            pygame.draw.line(self.layer, (95, 240, 185, 155), center + safe * 125,
                             center + safe * radius, 2)
        screen.blit(self.layer, (0, 0))

    def draw_hud(self, screen, boss, player):
        if boss is None or boss.intro_timer > 0 or boss.health <= 0:
            return
        laser = boss.beam_warning or boss.beam_active
        warning = boss.warning and boss.attack_name in ("ION STORM", "RIFT AMBUSH", "REAPER BLADES")
        critical = player.health <= 2
        if not laser and not warning and not critical and not boss.enraged:
            return
        self.layer.fill((0, 0, 0, 0))
        pulse = (math.sin(boss.animation_time * 7) + 1) / 2
        alpha = round(130 + 35 * pulse) if laser or warning else 65
        # Red edge strips leave the ship and bullets visible in the middle.
        for inset in range(0, 24, 4):
            color = (225, 25, 55, max(0, alpha - inset * 5))
            pygame.draw.rect(self.layer, color, (inset, 78 + inset,
                             self.width - inset * 2, self.height - 120 - inset * 2), 4)
        screen.blit(self.layer, (0, 0))
        if not laser and not warning:
            text = "HULL CRITICAL" if critical else "BOSS ENRAGED"
            label = self.label(text, self.hint_font, (255, 115, 120))
            screen.blit(label, label.get_rect(midtop=(self.width // 2, 145)))
            return

        if boss.beam_warning:
            title = "DANGER - DEATHRAY CHARGING"
            hint = "GET BEHIND THE BOSS  |  HOLD SPACE FOR NITRO"
            duration = boss.beam_warning_duration
        elif boss.beam_active:
            title = "DEATHRAY ACTIVE"
            hint = "STAY CLEAR OF THE SWEEP"
            duration = boss.beam_duration
        elif boss.attack_name == "ION STORM":
            title = "DANGER - ION STORM"
            hint = "MOVE BETWEEN THE PURPLE LANES"
            duration = 1.05
        elif boss.attack_name == "REAPER BLADES":
            title = "DANGER - REAPER BLADES"
            hint = "BLADES RETURN - MOVE BETWEEN THE LANES"
            duration = 0.9
        else:
            title = "DANGER - RIFT AMBUSH"
            hint = "LEAVE THE MARKED LANDING ZONE"
            duration = boss.rift_warning_duration

        panel = pygame.Rect(self.width // 2 - 320, 148, 640, 77)
        pygame.draw.rect(screen, (32, 10, 22), panel, border_radius=5)
        pygame.draw.rect(screen, (255, 85, 105), panel, 2, border_radius=5)
        title_image = self.label(title, self.title_font, (255, 215, 205))
        hint_image = self.label(hint, self.hint_font, (255, 175, 150))
        screen.blit(title_image, (panel.x + 16, panel.y + 9))
        screen.blit(hint_image, (panel.x + 16, panel.y + 43))
        seconds = math.ceil(max(0, boss.timer) * 10) / 10
        timer = self.label(f"{seconds:.1f}", self.timer_font, (255, 100, 110))
        screen.blit(timer, timer.get_rect(midright=(panel.right - 17, panel.y + 35)))
        progress = max(0, min(1, 1 - boss.timer / duration))
        pygame.draw.rect(screen, (80, 25, 40), (panel.x + 3, panel.bottom - 7, panel.width - 6, 4))
        pygame.draw.rect(screen, (255, 100, 110), (panel.x + 3, panel.bottom - 7,
                         round((panel.width - 6) * progress), 4))
