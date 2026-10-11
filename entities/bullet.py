import pygame

import theme


class Bullet:
    _image = None

    def __init__(self, x, y, dx=0.0, speed=8):
        self.width = 32
        self.height = 32

        if Bullet._image is None:
            Bullet._image = theme.load_image(
                "assets/images/shabullet.png",
                (self.width, self.height),
                lambda: theme.make_orb(32, theme.ACCENT),
            )

        self.image = Bullet._image
        self.x = x
        self.y = y
        self.dx = dx
        self.speed = speed
        self.is_active = True

    def update(self):
        self.y -= self.speed
        self.x += self.dx

        if (
            self.y < -self.height
            or self.x < -self.width
            or self.x > 800
        ):
            self.is_active = False

    def get_rect(self):
        return pygame.Rect(
            int(self.x), int(self.y), self.width, self.height
        )

    def draw(self, screen):
        if self.is_active:
            screen.blit(self.image, (int(self.x), int(self.y)))