import math

import pygame

import theme
from db import login_player, register_player
from sound import audio

USERNAME_MIN = 3
USERNAME_MAX = 16
PASSWORD_MIN = 6
PASSWORD_MAX = 32


FIELDS = {
    "login": [
        ("username", "Username", "user", False),
        ("password", "Password", "lock", True),
    ],
    "create": [
        ("username", "Username", "user", False),
        ("password", "Password", "lock", True),
        ("confirm", "Confirm Password", "lock", True),
    ],
}

PAGES = {
    "login": {
        "title": "ACCOUNT LOGIN",
        "button": "LOGIN",
        "button_icon": "arrow_right",
        "prompt": "Don't have an account?",
        "link": "Create Account",
        "link_icon": "user",
        "other": "create",
    },
    "create": {
        "title": "CREATE ACCOUNT",
        "button": "CREATE ACCOUNT",
        "button_icon": "plus",
        "prompt": "Already have an account?",
        "link": "Login",
        "link_icon": "arrow_right",
        "other": "login",
    },
}


class LoginManager:
    def __init__(self, screen, w, h):
        self.screen = screen
        self.w = w
        self.h = h

        self.backdrop = theme.Backdrop(
            w, h, image="assets/images/shaback.png"
        )

        self.page = "login"
        self.values = {"username": "", "password": "", "confirm": ""}
        self.show = {"password": False, "confirm": False}
        self.focus = 0

        self.message = ""
        self.message_color = theme.BAD
        self.message_timer = 0
        self.shake = 0

        self.logged_in_player = None

    def reset(self):
        self.logged_in_player = None
        self.page = "login"
        self.values = {"username": "", "password": "", "confirm": ""}
        self.show = {"password": False, "confirm": False}
        self.focus = 0
        self.message = ""
        self.message_timer = 0

    def switch(self, page):
        self.page = page
        self.values["password"] = ""
        self.values["confirm"] = ""
        self.show = {"password": False, "confirm": False}
        self.focus = 0
        self.message = ""
        self.message_timer = 0

    def error(self, message):
        self.message = message
        self.message_color = theme.BAD
        self.message_timer = 200
        self.shake = 18

    def notice(self, message):
        self.message = message
        self.message_color = theme.GOOD
        self.message_timer = 200

    def layout(self, ox=0):
        pw = 360
        count = len(FIELDS[self.page])
        ph = 84 + count * 52 + 8 + 46 + 56
        px = self.w - 30 - pw + ox
        py = (self.h - ph) // 2 - 10

        panel = pygame.Rect(px, py, pw, ph)

        rects = [
            pygame.Rect(px + 28, py + 78 + i * 52, pw - 56, 42)
            for i in range(count)
        ]

        submit = pygame.Rect(px + 28, py + 78 + count * 52 + 8, pw - 56, 46)

        info = PAGES[self.page]
        prompt_w = theme.font(14, False).size(info["prompt"])[0]
        link_w = theme.font(16, True).size(info["link"])[0]
        total = prompt_w + 12 + 26 + link_w
        start = px + pw // 2 - total // 2

        link = pygame.Rect(
            start + prompt_w + 12, submit.bottom + 14, 26 + link_w, 28
        )

        return panel, rects, submit, link

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.click(event.pos)

            elif event.type == pygame.KEYDOWN:
                self.key(event)

    def click(self, pos):
        panel, rects, submit, link = self.layout()

        if link.collidepoint(pos):
            audio.play_click()
            self.switch(PAGES[self.page]["other"])
            return

        for i, (key, _label, _icon, secret) in enumerate(FIELDS[self.page]):
            eye = pygame.Rect(rects[i].right - 48, rects[i].y, 48, rects[i].h)

            if secret and eye.collidepoint(pos):
                audio.play_click()
                self.show[key] = not self.show[key]
                self.focus = i
                return

            if rects[i].collidepoint(pos):
                self.focus = i
                return

        if submit.collidepoint(pos):
            audio.play_click()
            self.submit()

    def key(self, event):
        fields = FIELDS[self.page]

        if event.key == pygame.K_TAB:
            step = -1 if event.mod & pygame.KMOD_SHIFT else 1
            self.focus = (self.focus + step) % len(fields)

        elif event.key == pygame.K_DOWN:
            self.focus = (self.focus + 1) % len(fields)

        elif event.key == pygame.K_UP:
            self.focus = (self.focus - 1) % len(fields)

        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.focus < len(fields) - 1:
                self.focus += 1
            else:
                self.submit()

        elif event.key == pygame.K_BACKSPACE:
            name = fields[self.focus][0]
            self.values[name] = self.values[name][:-1]

        else:
            ch = event.unicode
            name = fields[self.focus][0]

            if not ch or not ch.isprintable():
                return

            if name == "username":
                if len(self.values[name]) >= USERNAME_MAX:
                    return

                if not (ch.isascii() and (ch.isalnum() or ch in "_.")):
                    return
            else:
                if len(self.values[name]) >= PASSWORD_MAX or ch == " ":
                    return

            self.values[name] += ch

    def submit(self):
        username = self.values["username"].strip()
        password = self.values["password"]

        if self.page == "login":
            if not username or not password:
                self.error("FILL IN ALL FIELDS")
                return

            player, message = login_player(username, password)

            if player:
                self.logged_in_player = player
                self.values = {"username": "", "password": "", "confirm": ""}
                self.message = ""
            else:
                self.error(message)

            return

        confirm = self.values["confirm"]

        if len(username) < USERNAME_MIN:
            self.error("USERNAME TOO SHORT")
        elif len(password) < PASSWORD_MIN:
            self.error("PASSWORD TOO SHORT")
        elif password != confirm:
            self.error("PASSWORDS DO NOT MATCH")
        else:
            ok, message = register_player(username, password)

            if ok:
                self.switch("login")
                self.values["username"] = username
                self.focus = 1
                self.notice(message)
            else:
                self.error(message)

    def draw_field(self, rect, key, label, icon_name, secret, focused):
        s = self.screen

        theme.panel(
            s,
            rect,
            border=theme.BORDER_HI if focused else theme.BORDER,
            fill=theme.FIELD,
            glow=focused,
            cut=8,
        )

        theme.icon(
            s,
            icon_name,
            rect.x + 28,
            rect.centery,
            theme.LAVENDER if focused else theme.TEXT_DIM,
            1.0,
        )

        value = self.values[key]
        text_x = rect.x + 56
        end_x = text_x

        if not value:
            theme.text(
                s,
                label,
                18,
                theme.TEXT_DIM,
                (text_x, rect.centery),
                anchor="midleft",
                bold=False,
            )
        elif secret and not self.show[key]:
            step = min(13, (rect.w - 56 - 52) // max(1, len(value)))

            for i in range(len(value)):
                pygame.draw.circle(
                    s,
                    theme.TEXT,
                    (text_x + 5 + i * step, rect.centery),
                    4,
                )

            end_x = text_x + len(value) * step
        else:
            r = theme.text(
                s,
                value,
                20,
                theme.TEXT,
                (text_x, rect.centery),
                anchor="midleft",
                bold=False,
            )
            end_x = r.right

        if focused and (pygame.time.get_ticks() // 500) % 2 == 0:
            pygame.draw.line(
                s,
                theme.LAVENDER,
                (end_x + 2, rect.centery - 11),
                (end_x + 2, rect.centery + 11),
                2,
            )

        if secret:
            theme.icon(
                s,
                "eye" if self.show[key] else "eye_off",
                rect.right - 28,
                rect.centery,
                theme.TEXT_DIM,
                0.9,
            )

    def draw_title(self):
        cx = 190

        theme.fancy_text(
            self.screen,
            "SPACE",
            76,
            (cx, 150),
            fill=(255, 255, 255),
            extrude=(140, 96, 255),
            max_width=300,
        )
        theme.fancy_text(
            self.screen,
            "INVADERS",
            76,
            (cx, 230),
            fill=(255, 240, 252),
            extrude=(236, 78, 206),
            max_width=300,
        )

    def draw(self):
        s = self.screen
        mouse = pygame.mouse.get_pos()
        info = PAGES[self.page]

        self.backdrop.draw(s)
        self.draw_title()

        ox = 0

        if self.shake > 0:
            ox = int(math.sin(self.shake * 1.6) * 8)
            self.shake -= 1

        panel, rects, submit, link = self.layout(ox)

        theme.panel(s, panel)

        title = theme.glow_text(
            s,
            info["title"],
            22,
            theme.TEXT,
            theme.BTN,
            (panel.centerx + 16, panel.y + 42),
        )
        theme.icon(s, "user", title.left - 26, panel.y + 42, theme.LAVENDER, 1.3)

        for i, (key, label, icon_name, secret) in enumerate(FIELDS[self.page]):
            self.draw_field(
                rects[i], key, label, icon_name, secret, i == self.focus
            )

        theme.button(
            s,
            submit,
            info["button"],
            mouse,
            icon_name=info["button_icon"],
            primary=True,
            size=20,
        )

        hover = link.collidepoint(mouse)
        link_color = (190, 240, 255) if hover else theme.CYAN

        theme.text(
            s,
            info["prompt"],
            14,
            theme.TEXT_DIM,
            (link.x - 12, link.centery),
            anchor="midright",
            bold=False,
        )
        theme.icon(s, info["link_icon"], link.x + 10, link.centery, theme.LAVENDER, 0.9)
        theme.text(
            s, info["link"], 16, link_color,
            (link.x + 26, link.centery), anchor="midleft",
        )
        pygame.draw.line(
            s, link_color,
            (link.x + 26, link.bottom - 3), (link.right, link.bottom - 3), 1,
        )

        if self.message_timer > 0:
            self.message_timer -= 1
            theme.text(
                s,
                self.message,
                18,
                self.message_color,
                (panel.centerx, panel.bottom + 28),
                anchor="center",
            )