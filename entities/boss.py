import pygame

import theme


class EnemyShot:
    _image = None

    def __init__(self, x, y, vx, vy):
        if EnemyShot._image is None:
            EnemyShot._image = theme.make_orb(26, theme.BAD)

        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.active = True

    def update(self):
        self.x += self.vx
        self.y += self.vy

        if self.y > 660 or self.x < -40 or self.x > 840:
            self.active = False

    def get_rect(self):
        return pygame.Rect(int(self.x) + 6, int(self.y) + 6, 14, 14)

    def draw(self, screen):
        if self.active:
            screen.blit(EnemyShot._image, (int(self.x), int(self.y)))


class Boss:
    def __init__(self, level, screen_width):
        self.width = 170
        self.height = 150
        self.screen_width = screen_width

        self.max_hp = 25 + level * 5
        self.hp = self.max_hp

        self.image = theme.load_image(
            "assets/images/shamy.png",
            (self.width, self.height),
            lambda: theme.make_invader(
                (self.width, self.height), theme.ACCENT
            ),
        )

        self.x = screen_width / 2 - self.width / 2
        self.y = -self.height - 20

        self.state = "entering"
        self.dir = 1
        self.speed = min(1.8 + level * 0.12, 4.0)
        self.active = True

        self.level = level
        self.interval = max(35, 80 - level * 2)
        self.shoot_timer = 90
        self.flash = 0

    def update(self):
        shots = []

        if not self.active:
            return shots

        if self.state == "entering":
            self.y += 2

            if self.y >= 60:
                self.y = 60
                self.state = "fighting"
        else:
            self.x += self.dir * self.speed

            if self.x < 10:
                self.x = 10
                self.dir = 1
            elif self.x > self.screen_width - self.width - 10:
                self.x = self.screen_width - self.width - 10
                self.dir = -1

            self.shoot_timer -= 1

            if self.shoot_timer <= 0:
                self.shoot_timer = self.interval

                cx = self.x + self.width / 2 - 13
                cy = self.y + self.height - 20

                if self.level >= 10:
                    spread = (-4, -2, 0, 2, 4)
                else:
                    spread = (-2.2, 0, 2.2)

                for vx in spread:
                    shots.append(EnemyShot(cx, cy, vx, 5.5))

        if self.flash > 0:
            self.flash -= 1

        return shots

    def hit(self, damage=1):
        self.hp -= damage
        self.flash = 4

        if self.hp <= 0:
            self.hp = 0
            self.active = False
            return True

        return False

    def get_rect(self):
        return pygame.Rect(
            int(self.x) + 15,
            int(self.y) + 10,
            self.width - 30,
            self.height - 20,
        )

    def draw(self, screen):
        if not self.active:
            return

        screen.blit(self.image, (int(self.x), int(self.y)))