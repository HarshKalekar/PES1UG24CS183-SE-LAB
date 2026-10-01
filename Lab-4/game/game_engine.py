import math
import pygame
from game.player import Player
from game.world import generate_platforms, draw_lava, CRUMBLE, SPRING

WIDTH, HEIGHT = 500, 640
FPS = 60
BG = (20, 15, 30)
GROUND_Y = HEIGHT + 200

LAVA_BASE_RISE = 0.4
LAVA_MAX_RISE = 1.2
SPRING_VEL = -22              # double the normal jump velocity (-13 -> ~-22)

BURST_INTERVAL = 15 * FPS     # a burst every 15 seconds
BURST_DURATION = 3 * FPS      # lasting 3 seconds
BURST_WARNING = int(1.5 * FPS)  # warning flashes this long before the burst
BURST_MULT = 2.0              # lava speed multiplier during a burst


class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Lava Escape")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 24, bold=True)
        self.small_font = pygame.font.SysFont("monospace", 16, bold=True)
        self.big_font = pygame.font.SysFont("monospace", 42, bold=True)
        self.reset()

    def reset(self):
        self.platforms = generate_platforms(WIDTH, GROUND_Y)
        self.player = Player(WIDTH // 2 - 16, GROUND_Y - 50)
        # start the camera so the player and ground are visible on screen
        self.cam_y = GROUND_Y - HEIGHT + 120
        self.lava_y = GROUND_Y + 60
        self.lava_rise = LAVA_BASE_RISE
        self.score = 0
        self.game_over = False
        self.won = False
        self.top_y = self.platforms[-1].rect.y
        self.frame = 0

    # ---- lava burst helpers ------------------------------------------------
    @property
    def burst_active(self):
        return self.frame >= BURST_INTERVAL and self.frame % BURST_INTERVAL < BURST_DURATION

    @property
    def burst_warning(self):
        return (not self.burst_active
                and self.frame % BURST_INTERVAL >= BURST_INTERVAL - BURST_WARNING)

    @property
    def lava_speed(self):
        return self.lava_rise * (BURST_MULT if self.burst_active else 1.0)

    # ---- main loop pieces --------------------------------------------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r: self.reset()
        return True

    def update(self):
        if self.game_over or self.won: return
        keys = pygame.key.get_pressed()
        self.player.update(keys, self.platforms, WIDTH)

        # react to the platform the player just landed on
        landed = self.player.landed_on
        if landed is not None:
            if landed.kind == CRUMBLE:
                landed.trigger_crumble()
            elif landed.kind == SPRING:
                landed.trigger_bounce()
                self.player.launch(SPRING_VEL)

        # advance platform timers; crumbled platforms vanish from the list
        self.platforms = [p for p in self.platforms if not p.update()]

        target = self.player.rect.centery - HEIGHT // 2
        if target < self.cam_y: self.cam_y = target
        self.lava_y -= self.lava_speed
        self.lava_rise = min(LAVA_MAX_RISE, self.lava_rise + 0.0003)
        self.score = max(0, (GROUND_Y - self.player.rect.y) // 10)
        self.frame += 1
        if self.player.rect.bottom >= self.lava_y:
            self.game_over = True
        if self.player.rect.top <= self.top_y - 20:
            self.won = True

    def draw(self):
        self.screen.fill(BG)
        for p in self.platforms:
            p.draw(self.screen, self.cam_y)
        self.player.draw(self.screen, self.cam_y)
        draw_lava(self.screen, self.lava_y, self.cam_y, WIDTH, HEIGHT, self.frame)
        self._draw_burst_tint()
        sc = self.font.render(f"Height: {self.score}m  R=Restart", True, (220, 200, 180))
        self.screen.blit(sc, (8, 10))
        self._draw_danger_meter()
        self._draw_burst_banner()
        if self.game_over:
            self._msg("LAVA GOT YOU!", (220, 80, 40))
        if self.won:
            self._msg("ESCAPED!", (80, 220, 100))
        pygame.display.flip()

    def _draw_danger_meter(self):
        # fill follows lava_rise (0.4 -> 1.2); a burst adds a flashing full-red state
        frac = (self.lava_rise - LAVA_BASE_RISE) / (LAVA_MAX_RISE - LAVA_BASE_RISE)
        frac = max(0.0, min(1.0, frac))
        x, y, w, h = 8, 42, 220, 16
        if self.burst_active:
            frac = 1.0
        pygame.draw.rect(self.screen, (50, 40, 60), (x, y, w, h), border_radius=4)
        # green -> yellow -> red as danger grows
        color = (int(60 + 195 * frac), int(200 - 150 * frac), 50)
        if self.burst_active and (self.frame // 6) % 2 == 0:
            color = (255, 240, 120)
        if frac > 0:
            pygame.draw.rect(self.screen, color, (x, y, max(6, int(w * frac)), h), border_radius=4)
        pygame.draw.rect(self.screen, (220, 200, 180), (x, y, w, h), 2, border_radius=4)
        label = f"DANGER  lava {self.lava_speed * FPS:.0f}px/s"
        self.screen.blit(self.small_font.render(label, True, (220, 200, 180)), (x + w + 10, y))

    def _draw_burst_tint(self):
        if self.burst_active or self.burst_warning:
            pulse = (math.sin(self.frame * 0.3) + 1) / 2
            alpha = int((70 if self.burst_active else 35) * (0.4 + 0.6 * pulse))
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(ov, (255, 40, 0, alpha), (0, 0, WIDTH, HEIGHT), 18)
            self.screen.blit(ov, (0, 0))

    def _draw_burst_banner(self):
        if not (self.burst_active or self.burst_warning) or (self.frame // 8) % 2:
            return
        if self.burst_active:
            left = (BURST_DURATION - self.frame % BURST_INTERVAL) / FPS
            text, color = f"!! LAVA BURST !! {left:.1f}s", (255, 90, 40)
        else:
            text, color = "WARNING: LAVA SURGE INCOMING", (255, 210, 60)
        t = self.font.render(text, True, color) if self.burst_active else self.small_font.render(text, True, color)
        self.screen.blit(t, (WIDTH // 2 - t.get_width() // 2, 72))

    def _msg(self, text, color):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        self.screen.blit(ov, (0, 0))
        m = self.big_font.render(text, True, color)
        s = self.font.render("Press R to Play Again", True, (200, 200, 200))
        self.screen.blit(m, (WIDTH // 2 - m.get_width() // 2, HEIGHT // 2 - 40))
        self.screen.blit(s, (WIDTH // 2 - s.get_width() // 2, HEIGHT // 2 + 20))

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
