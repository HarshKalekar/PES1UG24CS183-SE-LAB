import math
import random
import pygame

PLATFORM_COLOR = (100, 80, 50)
CRUMBLE_COLOR = (150, 110, 80)
SPRING_COLOR = (245, 205, 40)
LAVA_COLOR = (220, 60, 20)

NORMAL, CRUMBLE, SPRING = "normal", "crumble", "spring"

CRUMBLE_FRAMES = 60      # 1 second at 60 FPS between landing and breaking
SPRING_ANIM_FRAMES = 20  # length of the spring recoil animation


class Platform:
    """A platform with a hitbox (`rect`) plus type-specific state/animation."""

    def __init__(self, x, y, w, h, kind=NORMAL):
        self.rect = pygame.Rect(x, y, w, h)
        self.kind = kind
        self.crumble_timer = None   # None = stable, otherwise frames left
        self.bounce_timer = 0       # frames left in spring recoil animation

    # ---- behaviour -------------------------------------------------------
    def trigger_crumble(self):
        if self.kind == CRUMBLE and self.crumble_timer is None:
            self.crumble_timer = CRUMBLE_FRAMES

    def trigger_bounce(self):
        self.bounce_timer = SPRING_ANIM_FRAMES

    def update(self):
        """Advance timers. Returns True when the platform should be removed."""
        if self.bounce_timer > 0:
            self.bounce_timer -= 1
        if self.crumble_timer is not None:
            self.crumble_timer -= 1
            return self.crumble_timer <= 0
        return False

    # ---- drawing ---------------------------------------------------------
    def draw(self, screen, cam_y):
        dr = self.rect.move(0, -int(cam_y))
        if self.kind == CRUMBLE:
            color = CRUMBLE_COLOR
            if self.crumble_timer is not None:
                # shake harder and glow redder as the platform is about to break
                t = 1 - self.crumble_timer / CRUMBLE_FRAMES
                dr.move_ip(random.randint(-2, 2), random.randint(-1, 1))
                color = tuple(int(a + (b - a) * t)
                              for a, b in zip(CRUMBLE_COLOR, (210, 70, 40)))
            pygame.draw.rect(screen, color, dr, border_radius=4)
            # crack marks so crumbling platforms are recognisable
            for cx in range(dr.left + 20, dr.right - 10, 40):
                pygame.draw.line(screen, (70, 50, 30), (cx, dr.top + 2), (cx + 6, dr.bottom - 3), 2)
        elif self.kind == SPRING:
            if self.bounce_timer > 0:
                # compress then overshoot: platform squashes down, then pops back
                phase = self.bounce_timer / SPRING_ANIM_FRAMES
                squash = int(math.sin(phase * math.pi) * 7)
                dr.top += squash
                dr.height = max(6, dr.height - squash)
            pygame.draw.rect(screen, SPRING_COLOR, dr, border_radius=4)
            pygame.draw.rect(screen, (255, 245, 150), (dr.left + 4, dr.top + 1, dr.width - 8, 3), border_radius=2)
            # little up-arrows
            for cx in range(dr.left + 25, dr.right - 15, 40):
                mid = dr.top + dr.height // 2 + 2
                pygame.draw.lines(screen, (150, 100, 10), False,
                                  [(cx - 5, mid + 3), (cx, mid - 3), (cx + 5, mid + 3)], 2)
        else:
            pygame.draw.rect(screen, PLATFORM_COLOR, dr, border_radius=4)


def generate_platforms(width, base_y, count=30):
    plats = [Platform(0, base_y, width, 20)]  # ground (always stable)
    y = base_y - 110
    prev_kind = NORMAL
    for i in range(count):
        w = random.randint(80, 200)
        x = random.randint(0, width - w)
        kind = NORMAL
        # keep the first and last (goal) platforms normal, and never put two
        # special platforms back-to-back so every level stays beatable
        if 0 < i < count - 1 and prev_kind == NORMAL:
            r = random.random()
            if r < 0.20:
                kind = CRUMBLE
            elif r < 0.35:
                kind = SPRING
        plats.append(Platform(x, y, w, 16, kind))
        prev_kind = kind
        y -= random.randint(80, 130)
    return plats


def draw_lava(screen, lava_y, cam_y, width, height, frame):
    ly = int(lava_y - cam_y)
    if ly < height:
        # lava surface wave
        pts = [(0, ly)]
        for x in range(0, width + 20, 20):
            pts.append((x, ly + int(math.sin(x * 0.08 + frame * 0.1) * 8)))
        pts.append((width, height))
        pts.append((0, height))
        pygame.draw.polygon(screen, LAVA_COLOR, pts)
        # glow
        s = pygame.Surface((width, 30), pygame.SRCALPHA)
        for i in range(15):
            pygame.draw.line(s, (255, 100, 0, max(0, 60 - i * 4)), (0, i), (width, i), 1)
        screen.blit(s, (0, ly - 15))
