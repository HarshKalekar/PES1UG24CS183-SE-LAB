import pygame

SPEED = 4
JUMP_VEL = -13
GRAVITY = 0.55
MAX_FALL = 12
LAND_TOLERANCE = 2          # px a foot may already be inside a platform top
STRETCH_FRAMES = 14         # length of the spring launch squash-and-stretch


class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.vel_y = 0
        self.on_ground = False
        self.color = (60, 160, 220)
        self.landed_on = None   # Platform landed on during the latest update()
        self.stretch = 0        # frames left of spring-launch animation

    def launch(self, vel):
        """Used by spring platforms to fling the player upward."""
        self.vel_y = vel
        self.on_ground = False
        self.stretch = STRETCH_FRAMES

    def update(self, keys, platforms, width):
        dx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx = -SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx = SPEED
        if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and self.on_ground:
            self.vel_y = JUMP_VEL
            self.on_ground = False

        self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL)
        self.rect.x = max(0, min(width - self.rect.width, self.rect.x + dx))

        prev_bottom = self.rect.bottom          # feet position BEFORE moving this frame
        self.rect.y += int(self.vel_y)
        if self.stretch > 0:
            self.stretch -= 1
        self.on_ground = False
        self.landed_on = None

        # One-way platforms: only land when moving down AND the feet were at or
        # above the platform's top edge before this frame's movement.
        for p in platforms:
            r = p.rect
            overlaps_x = self.rect.right > r.left and self.rect.left < r.right
            if (overlaps_x
                    and self.vel_y > 0
                    and prev_bottom <= r.top + LAND_TOLERANCE
                    and self.rect.bottom >= r.top):
                self.rect.bottom = r.top
                self.vel_y = 0
                self.on_ground = True
                self.landed_on = p
                break

    def draw(self, screen, cam_y):
        dr = self.rect.move(0, -int(cam_y))
        if self.stretch > 0:
            # squash-and-stretch recoil after a spring launch
            s = self.stretch / STRETCH_FRAMES
            extra_h, less_w = int(12 * s), int(8 * s)
            dr = pygame.Rect(dr.x + less_w // 2, dr.y - extra_h, dr.width - less_w, dr.height + extra_h)
        pygame.draw.rect(screen, self.color, dr, border_radius=6)
        pygame.draw.circle(screen, (255, 220, 180), (dr.centerx, dr.top + 8), 7)
