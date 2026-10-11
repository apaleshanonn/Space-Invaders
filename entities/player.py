import os

import pygame

import theme

# Ship 1: assets/images/shanship.png (imong original). Ship 2-4: ship2.png ... ship4.png
# Kung wala ang file, gi-drawing ang ship (lahi-lahi nga kulay).
SHIP_FILES = (
    ("shanship.png", "shaship.png"),
    ("ship2.png",),
    ("ship3.png",),
    ("ship4.png",),
)
SHIP_COUNT = len(SHIP_FILES)
SHIP_DIRS = ("assets/images", "assets")

_ship_cache = {}
_warned = False


def find_ship_file(index=0):
    here = os.path.dirname(os.path.abspath(__file__))
    roots = [os.getcwd(), here, os.path.dirname(here)]

    for name in SHIP_FILES[index % SHIP_COUNT]:
        for root in roots:
            for sub in SHIP_DIRS:
                folder = os.path.join(root, sub)

                if not os.path.isdir(folder):
                    continue

                for found in os.listdir(folder):
                    if found.lower() == name:
                        return os.path.join(folder, found)

    return None


def load_ship(width, height, index=0):
    path = find_ship_file(index)

    if path:
        try:
            image = pygame.image.load(path).convert_alpha()
            iw, ih = image.get_size()
            scale = min(width / iw, height / ih)
            size = (max(1, int(iw * scale)), max(1, int(ih * scale)))
            image = pygame.transform.smoothscale(image, size)

            surf = pygame.Surface((width, height), pygame.SRCALPHA)
            surf.blit(image, image.get_rect(center=(width // 2, height // 2)))
            return surf
        except (pygame.error, OSError):
            pass

    global _warned

    if index == 0 and not _warned:
        _warned = True
        print("Player image not found: assets/images/shanship.png")

    return theme.make_ship((width, height), index)


def get_ship_image(index, width, height):
    key = (index, width, height)

    if key not in _ship_cache:
        _ship_cache[key] = load_ship(width, height, index)

    return _ship_cache[key]


class Player:
    BLINK_FRAMES = 60

    def __init__(self, screen_width, screen_height, ship=0):
        self.width = 80
        self.height = 80
        self.speed = 5

        self.image = get_ship_image(ship, self.width, self.height)
        self.x = screen_width // 2 - self.width // 2
        self.y = screen_height - 100
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.is_blinking = False
        self.blink_timer = 0
        self.visible = True

        self.shield = False
        self.invuln = 0

    def move_left(self):
        if not self.is_blinking:
            self.x -= self.speed

    def move_right(self):
        if not self.is_blinking:
            self.x += self.speed

    def keep_inside_screen(self):
        self.x = max(0, min(self.x, self.screen_width - self.width))

    def get_rect(self):
        return pygame.Rect(
            int(self.x), int(self.y), self.width, self.height
        )

    def start_blink(self):
        self.is_blinking = True
        self.blink_timer = 0
        self.visible = True

    def update_blink(self):
        if self.is_blinking:
            self.blink_timer += 1

            if self.blink_timer % 6 == 0:
                self.visible = not self.visible

            if self.blink_timer >= self.BLINK_FRAMES:
                self.is_blinking = False
                self.visible = True
        else:
            self.visible = True

    def update(self):
        keys = pygame.key.get_pressed()

        if not self.is_blinking:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.move_left()

            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.move_right()

        if self.invuln > 0:
            self.invuln -= 1

        self.keep_inside_screen()
        self.update_blink()

    def draw(self, screen):
        if self.visible:
            screen.blit(self.image, (int(self.x), int(self.y)))

        if self.shield:
            center = self.get_rect().center
            pygame.draw.circle(screen, theme.ICE, center, 54, 3)
            pygame.draw.circle(screen, (70, 130, 190), center, 58, 1)