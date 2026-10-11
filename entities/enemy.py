import math

import pygame

import theme


class Enemy:
    _file_image = None
    _fallbacks = {}

    def __init__(self, index, total_enemies, screen_width, speed=4, hp=1):
        self.width = 64
        self.height = 64
        self.index = index
        self.image = self._get_image(index)

        spacing = screen_width / (total_enemies + 1)

        self.target_mid_x = spacing * (index + 1) - self.width // 2
        self.target_mid_y = 85 + (40 if index % 2 == 0 else 0)

        self.x = self.target_mid_x
        self.y = -100

        self.state = "entering"
        self.speed = speed
        self.dx = 0
        self.dy = 0
        self.active = True

        self.hp = hp
        self.max_hp = hp
        self.tick = index * 25

    @classmethod
    def _get_image(cls, index):
        if cls._file_image is None:
            try:
                image = pygame.image.load(
                    "assets/images/shamy.png"
                ).convert_alpha()
                cls._file_image = pygame.transform.smoothscale(
                    image, (64, 64)
                )
            except (pygame.error, FileNotFoundError, OSError):
                cls._file_image = False

        if cls._file_image:
            return cls._file_image

        key = index % len(theme.INVADER_COLORS)

        if key not in cls._fallbacks:
            cls._fallbacks[key] = theme.make_invader(
                (64, 64), theme.INVADER_COLORS[key]
            )

        return cls._fallbacks[key]

    def start_drop(self, target_x, target_y):
        self.state = "dropping"

        distance_x = target_x - self.x
        distance_y = target_y - self.y

        distance = (distance_x ** 2 + distance_y ** 2) ** 0.5

        if distance > 0:
            self.dx = (distance_x / distance) * self.speed
            self.dy = (distance_y / distance) * self.speed
        else:
            self.dx = 0
            self.dy = self.speed

    def update(self):
        if not self.active:
            return

        if self.state == "entering":
            if self.y < self.target_mid_y:
                self.y += 3
            else:
                self.y = self.target_mid_y
                self.state = "waiting"

        elif self.state == "waiting":
            self.tick += 1
            self.x = self.target_mid_x + math.sin(self.tick * 0.04) * 14
            self.y = self.target_mid_y + math.sin(self.tick * 0.07) * 5

        elif self.state == "dropping":
            self.x += self.dx
            self.y += self.dy

            if self.y > 650 or self.x < -100 or self.x > 900:
                self.state = "offscreen"
                self.active = False

    def get_rect(self):
        return pygame.Rect(
            int(self.x), int(self.y), self.width, self.height
        )

    def draw(self, screen):
        if self.active and self.state != "offscreen":
            screen.blit(self.image, (int(self.x), int(self.y)))

            if self.max_hp > 1:
                for i in range(self.max_hp):
                    color = (
                        theme.ACCENT if i < self.hp else (60, 40, 110)
                    )
                    pygame.draw.rect(
                        screen,
                        color,
                        (int(self.x) + 8 + i * 20, int(self.y) - 6, 16, 4),
                        border_radius=2,
                    )