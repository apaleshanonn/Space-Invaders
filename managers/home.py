import math

import pygame

import theme
from entities.player import get_ship_image
from player_prefs import get_prefs
from sound import audio


class Home:
    def __init__(self, screen, w, h, player=None):
        self.screen = screen
        self.w = w
        self.h = h
        self.player = player
        self.action = None

        self.backdrop = theme.Backdrop(
            w, h, image="assets/images/shamenu.png"
        )

        specs = [
            ("play", "START GAME", "rocket"),
            ("profile", "PLAYER PROFILE", "user"),
            ("settings", "SETTINGS", "gear"),
            ("leaderboard", "LEADERBOARD", "trophy"),
            ("logout", "LOG OUT", "exit"),
        ]

        self.buttons = [
            (key, label, icon_name, pygame.Rect(w - 340, 126 + i * 68, 300, 54))
            for i, (key, label, icon_name) in enumerate(specs)
        ]

        pid = player.get("player_id") if isinstance(player, dict) else None
        self.ship = get_ship_image(get_prefs(pid)["ship"], 120, 120)

        self.invaders = [
            theme.make_invader((44, 34), color)
            for color in theme.INVADER_COLORS
        ]
        self.logo_invader = theme.make_invader((66, 50), theme.ACCENT)

        self.invader_spots = [
            (76, 360),
            (170, 332),
            (270, 360),
            (350, 332),
            (122, 410),
            (310, 412),
        ]

    def username(self):
        if isinstance(self.player, dict):
            return str(self.player.get("username", "PLAYER"))

        if self.player:
            return str(self.player)

        return "PLAYER"

    def draw(self):
        s = self.screen
        mouse = pygame.mouse.get_pos()
        t = pygame.time.get_ticks() / 1000.0

        self.backdrop.draw(s)

        for i, (x, y) in enumerate(self.invader_spots):
            bob = math.sin(t * 2 + i * 1.3) * 6
            img = self.invaders[i % len(self.invaders)]
            s.blit(img, img.get_rect(center=(x, int(y + bob))))

        ship_x, ship_y = 210, 505
        ship_y += int(math.sin(t * 2.2) * 4)

        for k in range(3):
            phase = (t * 1.4 + k / 3.0) % 1.0
            by = int(ship_y - 50 - phase * 150)
            alpha = int(255 * (1 - phase))
            beam = pygame.Surface((6, 22), pygame.SRCALPHA)
            beam.fill((*theme.ACCENT, max(0, alpha)))
            s.blit(beam, (ship_x - 3, by))

        s.blit(self.ship, self.ship.get_rect(center=(ship_x, ship_y)))

        cx = 200
        s.blit(self.logo_invader, self.logo_invader.get_rect(center=(cx, 62)))
        theme.fancy_text(
            s, "SPACE", 76, (cx, 140),
            fill=(255, 255, 255), extrude=(140, 96, 255), max_width=330,
        )
        theme.fancy_text(
            s, "INVADERS", 76, (cx, 222),
            fill=(255, 240, 252), extrude=(236, 78, 206), max_width=330,
        )

        theme.text(
            s,
            "WELCOME, " + self.username().upper(),
            16,
            theme.LAVENDER,
            (cx, 286),
            anchor="center",
        )

        for key, label, icon_name, rect in self.buttons:
            theme.button(
                s,
                rect,
                label,
                mouse,
                icon_name=icon_name,
                danger=(key == "logout"),
                size=19,
                align="left",
            )

    def handle_events(self, events):
        self.action = None

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.mouse_click(event.pos)

    def mouse_click(self, pos):
        for key, _label, _icon, rect in self.buttons:
            if rect.collidepoint(pos):
                audio.play_click()
                self.action = key
                return