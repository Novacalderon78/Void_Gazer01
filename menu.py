import pygame

import config
import effects


class Menu:
    def __init__(self, size):
        self.width, self.height = size
        self.scale = min(self.width / 1280, self.height / 800)
        self.left = (self.width - 1280 * self.scale) / 2
        self.top = (self.height - 800 * self.scale) / 2

        self.white = (225, 240, 250)
        self.muted = (135, 160, 185)
        self.cyan = (75, 220, 245)
        self.title_font = self.make_font(72)
        self.heading_font = self.make_font(42)
        self.score_font = self.make_font(64)
        self.button_font = self.make_font(29)
        self.card_font = self.make_font(25)
        self.small_font = self.make_font(21)
        self.detail_font = self.make_font(18)

        self.start_button = self.rect(388, 574, 240, 60)
        self.quit_button = self.rect(652, 574, 240, 60)
        self.again_button = self.rect(388, 500, 240, 60)
        self.menu_button = self.rect(652, 500, 240, 60)
        self.game_over_panel = self.rect(270, 186, 740, 428)

        # Render labels and enemy cards once; drawing a menu only blits them.
        self.title = self.title_font.render("VOID GAZER", True, self.white)
        self.subtitle = self.small_font.render("Larger enemy waves every 5,000 points", True, self.cyan)
        text = f"BOSS: VOID REAVER   |   AT {config.BOSS_SCORE_TARGET:,} POINTS   |   {config.BOSS_SCORE:,} BONUS   |   DEFEAT TO WIN"
        self.boss_hint = self.small_font.render(text, True, (255, 170, 95))
        self.enemy_label = self.detail_font.render("KNOW YOUR ENEMIES", True, self.muted)
        self.controls = self.small_font.render("WASD  Move    |    Mouse  Aim    |    Left click  Shoot    |    Hold Space  Nitro", True, self.white)
        self.pause_hint = self.detail_font.render("P  Pause    |    Esc  Quit", True, self.muted)
        self.start_hint = self.detail_font.render("Press ENTER to start", True, self.muted)
        self.over_title = self.heading_font.render("SHIP DESTROYED", True, (255, 135, 105))
        self.victory_title = self.heading_font.render("VICTORY!", True, (255, 215, 105))
        self.victory_subtitle = self.detail_font.render("VOID REAVER DEFEATED - GAME COMPLETE", True, self.cyan)
        self.final_label = self.detail_font.render("FINAL SCORE", True, self.muted)
        self.over_hint = self.detail_font.render("ENTER  Play again    |    M  Main menu", True, self.muted)
        self.button_labels = {
            "START GAME": self.button_font.render("START GAME", True, self.white),
            "QUIT": self.button_font.render("QUIT", True, self.white),
            "PLAY AGAIN": self.button_font.render("PLAY AGAIN", True, self.white),
            "MAIN MENU": self.button_font.render("MAIN MENU", True, self.white),
        }
        enemies = [
            ("yellow_enemy", "YELLOW  LV 1", 100, "2 HITS", "Predictive triple charge", (250, 215, 80)),
            ("green_enemy", "GREEN  LV 3", 300, "3 HITS", "4-shot burst + flank shots", (100, 230, 155)),
            ("red_enemy", "RED  LV 5", 600, "5 HITS", "Strafes + 3 spread volleys", (255, 110, 110)),
            ("ufo", "UFO  BONUS", 1000, "2 HITS", "Faster evasion; escapes 8s", (195, 155, 255)),
        ]
        self.cards = [self.make_card(*enemy) for enemy in enemies]
        self.best_score = None
        self.best_image = None
        self.last_result = None
        self.result_images = []

    def make_font(self, size):
        return pygame.font.Font(None, max(12, round(size * self.scale)))

    def rect(self, x, y, width, height):
        return pygame.Rect(round(self.left + x * self.scale), round(self.top + y * self.scale),
                           round(width * self.scale), round(height * self.scale))

    def centered(self, screen, image, x, y):
        point = (round(self.left + x * self.scale), round(self.top + y * self.scale))
        screen.blit(image, image.get_rect(center=point))

    def make_card(self, kind, name, score, hits, ability, color):
        width, height = round(238 * self.scale), round(280 * self.scale)
        card = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(card, (12, 22, 38, 242), card.get_rect(), border_radius=12)
        pygame.draw.rect(card, (40, 60, 80), card.get_rect(), width=1, border_radius=12)
        pygame.draw.line(card, color, (round(20 * self.scale), 0),
                         (width - round(20 * self.scale), 0), max(2, round(3 * self.scale)))

        labels = [
            (self.card_font.render(name, True, color), 30),
            (self.button_font.render(f"{score:,} POINTS", True, self.white), 204),
            (self.detail_font.render(hits, True, self.muted), 234),
            (self.detail_font.render(ability, True, self.muted), 259),
        ]
        for image, y in labels:
            card.blit(image, image.get_rect(center=(width // 2, round(y * self.scale))))

        sprite = effects.load_enemy_art(kind)[0][0]
        # Keep original sprite pixels at the normal window size.
        if self.scale < 1:
            side = max(1, round(128 * self.scale))
            sprite = pygame.transform.scale(sprite, (side, side))
        card.blit(sprite, sprite.get_rect(center=(width // 2, round(118 * self.scale))))
        return card

    def draw_button(self, screen, rectangle, label, mouse_position, primary=False):
        hovered = rectangle.collidepoint(mouse_position)
        color = (23, 104, 129) if primary else (20, 34, 53)
        border = self.cyan if primary else (80, 110, 140)
        if hovered:
            color = (30, 131, 153) if primary else (35, 56, 79)
            border = self.white
        pygame.draw.rect(screen, color, rectangle, border_radius=8)
        pygame.draw.rect(screen, border, rectangle, width=2, border_radius=8)
        image = self.button_labels[label]
        screen.blit(image, image.get_rect(center=rectangle.center))

    def draw_start(self, screen, mouse_position, best_score=0):
        self.centered(screen, self.title, 640, 97)
        self.centered(screen, self.subtitle, 640, 150)
        self.centered(screen, self.enemy_label, 640, 205)
        for number, card in enumerate(self.cards):
            screen.blit(card, self.rect(140 + number * 254, 235, 238, 280))
        self.centered(screen, self.boss_hint, 640, 544)

        self.draw_button(screen, self.start_button, "START GAME", mouse_position, True)
        self.draw_button(screen, self.quit_button, "QUIT", mouse_position)
        self.centered(screen, self.start_hint, 640, 656)
        self.centered(screen, self.controls, 640, 704)
        self.centered(screen, self.pause_hint, 640, 736)

        if best_score != self.best_score:
            self.best_score = best_score
            self.best_image = self.detail_font.render(f"SESSION BEST  {best_score:,}", True, self.cyan)
        if best_score > 0:
            self.centered(screen, self.best_image, 640, 773)

    def draw_game_over(self, screen, mouse_position, score, best_score, survival_time):
        self.draw_result(screen, mouse_position, score, best_score, survival_time)

    def draw_victory(self, screen, mouse_position, score, best_score, survival_time):
        self.draw_result(screen, mouse_position, score, best_score, survival_time, won=True)

    def draw_result(self, screen, mouse_position, score, best_score, survival_time, won=False):
        pygame.draw.rect(screen, (10, 19, 33), self.game_over_panel, border_radius=14)
        border = (175, 145, 65) if won else (65, 93, 119)
        pygame.draw.rect(screen, border, self.game_over_panel, width=2, border_radius=14)
        self.centered(screen, self.victory_title if won else self.over_title, 640, 245)
        if won:
            self.centered(screen, self.victory_subtitle, 640, 279)
        self.centered(screen, self.final_label, 640, 305)

        seconds = max(0, int(survival_time))
        result = (score, best_score, seconds, won)
        if result != self.last_result:
            self.last_result = result
            time_label = "COMPLETION TIME" if won else "TIME SURVIVED"
            self.result_images = [
                self.score_font.render(f"{score:,}", True, self.cyan),
                self.small_font.render(f"SESSION BEST  {best_score:,}", True, self.white),
                self.small_font.render(f"{time_label}  {seconds // 60:02d}:{seconds % 60:02d}", True, self.muted),
            ]
        for image, y in zip(self.result_images, (355, 412, 446)):
            self.centered(screen, image, 640, y)

        self.draw_button(screen, self.again_button, "PLAY AGAIN", mouse_position, True)
        self.draw_button(screen, self.menu_button, "MAIN MENU", mouse_position)
        self.centered(screen, self.over_hint, 640, 588)
