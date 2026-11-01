"""Firefly Flight - a night-forest flapper in Python + pygame.

Guide a glowing firefly between mushroom stumps and hanging moss.
Controls: Space / Up / W / left click = flutter, Esc = quit.
Requires: pip install pygame-ce
"""

import math
import random
import sys
from pathlib import Path

import pygame

W, H = 480, 720
GROUND = H - 70
GRAVITY = 1500.0
FLAP_V = -460.0
SPEED = 170.0
GAP = 190.0
TRUNK_W = 78
CAP_OVER = 12  # mushroom cap overhang past the trunk
SPACING = 260.0
FLY_X = 130.0
FLY_R = 12.0
# A packaged exe unpacks to a temp folder, so keep the score next to the exe instead.
APP_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
BEST_FILE = APP_DIR / "firefly_best.txt"
ICON_FILE = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "icon.png"

SKY_TOP = (8, 10, 36)
SKY_BOTTOM = (46, 28, 84)
GLOW = (190, 255, 110)


def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))


def sky_at(y):
    return lerp(SKY_TOP, SKY_BOTTOM, y / GROUND)


def make_glow(radius, color, strength=0.45):
    """Soft radial glow sprite, meant to be blitted with BLEND_RGB_ADD (black = no light)."""
    surf = pygame.Surface((radius * 2, radius * 2))
    for r in range(radius, 0, -2):
        k = strength * (1 - r / radius) ** 2
        pygame.draw.circle(surf, tuple(int(ch * k) for ch in color), (radius, radius), r)
    return surf


def make_moon():
    """Crescent moon: full disc with an offset disc erased to transparent."""
    surf = pygame.Surface((70, 70), pygame.SRCALPHA)
    pygame.draw.circle(surf, (250, 240, 200), (35, 35), 34)
    pygame.draw.circle(surf, (0, 0, 0, 0), (49, 25), 30)
    return surf


class Obstacle:
    def __init__(self, x, gap_y):
        self.x = x
        self.gap_y = gap_y
        self.scored = False

    def rects(self):
        x0 = self.x - CAP_OVER
        w = TRUNK_W + CAP_OVER * 2
        top = pygame.Rect(x0, 0, w, self.gap_y - GAP / 2)
        bottom_y = self.gap_y + GAP / 2
        bottom = pygame.Rect(x0, bottom_y, w, GROUND - bottom_y)
        return top, bottom


class Game:
    def __init__(self):
        self.t = 0.0
        self.scroll = 0.0
        self.best = self.load_best()
        self.stars = [(random.uniform(0, W), random.uniform(0, GROUND - 200), random.uniform(0, 6.28))
                      for _ in range(70)]
        self.sky = pygame.Surface((W, GROUND))
        for y in range(GROUND):
            pygame.draw.line(self.sky, sky_at(y), (0, y), (W, y))
        self.fly_glow = make_glow(90, GLOW)
        self.cap_glow = make_glow(80, (60, 230, 210))
        self.moon_glow = make_glow(110, (200, 190, 255), 0.25)
        self.moon = make_moon()
        self.font_big = pygame.font.SysFont("Segoe UI", 52, bold=True)
        self.font_mid = pygame.font.SysFont("Segoe UI", 32, bold=True)
        self.font_small = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.font_score = pygame.font.SysFont("Segoe UI", 64, bold=True)
        self.reset()

    # ---------- persistence ----------

    @staticmethod
    def load_best():
        try:
            return int(BEST_FILE.read_text())
        except (OSError, ValueError):
            return 0

    def save_best(self):
        try:
            BEST_FILE.write_text(str(self.best))
        except OSError:
            pass

    # ---------- game logic ----------

    def reset(self):
        self.state = "ready"
        self.y = H / 2
        self.vy = 0.0
        self.score = 0
        self.dead_time = 0.0
        self.obstacles = []
        self.sparks = []

    def spawn(self, x):
        self.obstacles.append(Obstacle(x, random.uniform(150, GROUND - 150)))

    def flap(self):
        if self.state == "ready":
            self.state = "playing"
            self.spawn(W + 60)
            self.vy = FLAP_V
        elif self.state == "playing":
            self.vy = FLAP_V
        elif self.dead_time > 0.6:
            self.reset()

    def die(self):
        self.state = "dead"
        self.dead_time = 0.0
        self.vy = -250.0
        if self.score > self.best:
            self.best = self.score
            self.save_best()

    def hits(self, rect):
        nx = max(rect.left, min(FLY_X, rect.right))
        ny = max(rect.top, min(self.y, rect.bottom))
        return (FLY_X - nx) ** 2 + (self.y - ny) ** 2 < FLY_R ** 2

    def update(self, dt):
        self.t += dt
        if self.state != "dead":
            self.scroll += SPEED * dt

        if self.state == "ready":
            self.y = H / 2 + math.sin(self.t * 3) * 10
        elif self.state == "playing":
            self.vy += GRAVITY * dt
            self.y += self.vy * dt
            if self.y < FLY_R:
                self.y, self.vy = FLY_R, 0.0

            for o in self.obstacles:
                o.x -= SPEED * dt
            if self.obstacles[-1].x < W - SPACING:
                self.spawn(self.obstacles[-1].x + SPACING)
            self.obstacles = [o for o in self.obstacles if o.x + TRUNK_W > -40]

            for o in self.obstacles:
                if not o.scored and o.x + TRUNK_W < FLY_X:
                    o.scored = True
                    self.score += 1
                if any(self.hits(r) for r in o.rects()):
                    self.die()
                    break
            if self.state == "playing" and self.y + FLY_R >= GROUND:
                self.die()
        else:
            self.dead_time += dt
            self.vy += GRAVITY * dt
            self.y = min(self.y + self.vy * dt, GROUND - FLY_R)

        # glowing trail: [x, y, vx, vy, life]
        if self.state != "dead":
            self.sparks.append([FLY_X - 8, self.y + 4, -SPEED * 0.4 - random.uniform(0, 60),
                                random.uniform(-30, 30), random.uniform(0.4, 0.8)])
        for s in self.sparks:
            s[0] += s[2] * dt
            s[1] += s[3] * dt
            s[4] -= dt
        self.sparks = [s for s in self.sparks if s[4] > 0]

    # ---------- drawing ----------

    def draw_sky(self, screen):
        screen.blit(self.sky, (0, 0))
        for sx, sy, phase in self.stars:
            tw = 0.5 + 0.5 * math.sin(self.t * 2 + phase)
            x = (sx - self.scroll * 0.03) % W
            screen.fill(lerp(sky_at(sy), (255, 250, 220), 0.3 + 0.7 * tw), (x, sy, 2, 2))

        # crescent moon
        screen.blit(self.moon_glow, (380 - 110, 110 - 110), special_flags=pygame.BLEND_RGB_ADD)
        screen.blit(self.moon, (380 - 35, 110 - 35))

    def draw_hills(self, screen, parallax, base, amp, freq, color):
        off = self.scroll * parallax
        pts = []
        for x in range(0, W + 12, 12):
            h = math.sin((x + off) * freq) * amp + math.sin((x + off) * freq * 2.3) * amp * 0.4
            pts.append((x, base - h))
        pts += [(W, GROUND), (0, GROUND)]
        pygame.draw.polygon(screen, color, pts)

    def draw_obstacle(self, screen, o):
        top_edge = o.gap_y - GAP / 2  # bottom of hanging moss
        bot_edge = o.gap_y + GAP / 2  # top of mushroom cap
        cx = o.x + TRUNK_W / 2

        # hanging moss curtain
        screen.fill((22, 42, 40), (o.x, 0, TRUNK_W, top_edge - 10))
        for i in range(4):
            screen.fill((30, 56, 50), (o.x + 8 + i * 18, 0, 4, top_edge - 14))
        for i in range(5):
            lx = o.x - 4 + i * (TRUNK_W + 8) / 4
            pygame.draw.ellipse(screen, (44, 96, 66), (lx - 14, top_edge - 24, 28, 24))
        # dangling vines with glowing berries
        for i in range(3):
            vx = o.x + 14 + i * 25
            length = 8 + 6 * math.sin(o.gap_y * 0.05 + i * 2.1)
            screen.fill((44, 96, 66), (vx, top_edge - 6, 2, length))
            pulse = 0.5 + 0.5 * math.sin(self.t * 4 + i)
            pygame.draw.circle(screen, lerp((160, 60, 120), (255, 140, 200), pulse),
                               (vx + 1, top_edge - 6 + length), 3)

        # tree stump
        screen.fill((34, 24, 40), (o.x, bot_edge + 18, TRUNK_W, GROUND - bot_edge - 18))
        for i in range(3):
            screen.fill((50, 36, 58), (o.x + 12 + i * 22, bot_edge + 30, 5, GROUND - bot_edge - 30))

        # glowing mushroom cap
        screen.blit(self.cap_glow, (cx - 80, bot_edge + 22 - 80), special_flags=pygame.BLEND_RGB_ADD)
        rx = TRUNK_W / 2 + CAP_OVER
        pygame.draw.ellipse(screen, (40, 190, 175), (cx - rx, bot_edge, rx * 2, 44))
        screen.fill((28, 120, 115), (o.x - CAP_OVER, bot_edge + 22, TRUNK_W + CAP_OVER * 2, 6))
        for dx, dy, r in ((-18, 10, 5), (14, 8, 4), (2, 16, 3)):
            pygame.draw.circle(screen, (200, 255, 240), (cx + dx, bot_edge + dy), r)

    def draw_ground(self, screen):
        screen.fill((12, 22, 20), (0, GROUND, W, H - GROUND))
        screen.fill((26, 52, 40), (0, GROUND, W, 6))
        x = -(self.scroll % 14)
        while x < W + 14:
            pygame.draw.polygon(screen, (30, 64, 46), [(x, GROUND), (x + 5, GROUND - 9), (x + 10, GROUND)])
            x += 14

    def draw_firefly(self, screen):
        alive = self.state != "dead"
        pulse = 0.5 + 0.5 * math.sin(self.t * 6)

        if alive:
            size = int(150 + pulse * 30)
            glow = pygame.transform.smoothscale(self.fly_glow, (size, size))
            screen.blit(glow, (FLY_X - 4 - size / 2, self.y + 2 - size / 2), special_flags=pygame.BLEND_RGB_ADD)

        # draw the bug upright on its own surface, then tilt it with velocity
        bug = pygame.Surface((48, 40), pygame.SRCALPHA)
        c = (24, 22)
        light = (220, 255, 120) if alive else (90, 100, 70)
        beat = math.sin(self.t * (40 if self.state == "playing" else 18))
        pygame.draw.ellipse(bug, light, (c[0] - 16, c[1] - 6, 20, 16))                 # glowing abdomen
        pygame.draw.ellipse(bug, (40, 30, 54), (c[0] - 3, c[1] - 7, 14, 12))           # thorax
        pygame.draw.ellipse(bug, (64, 42, 76), (c[0] + 6, c[1] - 6, 10, 8))            # head
        pygame.draw.circle(bug, (255, 255, 255), (c[0] + 13, c[1] - 3), 2)              # eye
        if alive:
            wh = 6 + abs(beat) * 8
            pygame.draw.ellipse(bug, (170, 190, 235, 200), (c[0] - 9, c[1] - 9 - beat * 3 - wh / 2, 20, wh))  # wing

        angle = max(-25, min(70, self.vy / 12)) if self.state != "ready" else 0
        bug = pygame.transform.rotate(bug, -angle)
        screen.blit(bug, bug.get_rect(center=(FLY_X, self.y)))

    def text(self, screen, s, y, font, color):
        shadow = font.render(s, True, (5, 5, 20))
        img = font.render(s, True, color)
        screen.blit(shadow, shadow.get_rect(midtop=(W / 2 + 3, y + 3)))
        screen.blit(img, img.get_rect(midtop=(W / 2, y)))

    def render(self, screen):
        self.draw_sky(screen)
        self.draw_hills(screen, 0.12, GROUND - 170, 30, 0.012, (26, 22, 62))
        self.draw_hills(screen, 0.30, GROUND - 80, 24, 0.02, (16, 18, 42))
        for o in self.obstacles:
            self.draw_obstacle(screen, o)
        self.draw_ground(screen)
        for x, y, _, _, life in self.sparks:
            screen.fill(lerp(sky_at(y), (230, 255, 140), life / 0.8), (x, y, 3, 3))
        self.draw_firefly(screen)

        if self.state == "ready":
            self.text(screen, "FIREFLY FLIGHT", 150, self.font_big, (220, 255, 130))
            self.text(screen, "Space / Click to flutter", 470, self.font_small, (230, 230, 255))
            self.text(screen, f"Best: {self.best}", 510, self.font_small, (170, 170, 210))
        elif self.state == "playing":
            self.text(screen, str(self.score), 40, self.font_score, (255, 255, 255))
        else:
            self.text(screen, "LIGHTS OUT", 190, self.font_big, (255, 150, 200))
            self.text(screen, f"Score: {self.score}", 270, self.font_mid, (255, 255, 255))
            self.text(screen, f"Best: {self.best}", 310, self.font_mid, (220, 255, 130))
            if self.dead_time > 0.6:
                self.text(screen, "Space / Click to try again", 380, self.font_small, (230, 230, 255))


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Firefly Flight")
    if ICON_FILE.exists():
        pygame.display.set_icon(pygame.image.load(ICON_FILE))
    clock = pygame.time.Clock()
    game = Game()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    game.flap()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                game.flap()

        dt = min(clock.tick(60) / 1000, 0.05)
        game.update(dt)
        game.render(screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
