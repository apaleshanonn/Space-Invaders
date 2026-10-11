import math

import pygame

import theme

KINDS = ["shield", "rapid", "triple", "life"]
WEIGHTS = [3, 3, 3, 1]

COLORS = {
    "shield": theme.ICE,
    "rapid": theme.GOLD,
    "triple": theme.ACCENT,
    "life": theme.BAD,
}

ICONS = {
    "shield": "shield",
    "rapid": "bolt",
    "triple": "triple",
    "life": "heart",
}


class PowerUp:
    def __init__(self, kind, x, y):
        self.kind = kind
        self.x = x
        self.y = y
        self.size = 36
        self.speed = 2.5
        self.tick = 0
        self.active = True

    def update(self):
        self.y += self.speed
        self.tick += 1

        if self.y > 640:
            self.active = False

    def get_rect(self):
        return pygame.Rect(
            int(self.x) - 18, int(self.y) - 18, self.size, self.size
        )

    def draw(self, screen):
        if not self.active:
            return

        color = COLORS[self.kind]
        center = (int(self.x), int(self.y))
        pulse = int(math.sin(self.tick * 0.15) * 3)

        pygame.draw.circle(screen, theme.FIELD, center, 18)
        pygame.draw.circle(screen, color, center, 18, 3)
        pygame.draw.circle(screen, color, center, 24 + pulse, 1)

        theme.icon(
            screen, ICONS[self.kind], center[0], center[1], color, 0.85
        )