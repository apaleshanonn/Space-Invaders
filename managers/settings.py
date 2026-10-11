import pygame

import theme
from settings_manager import load_settings, save_settings
from sound import audio


class SettingsScreen:
    def __init__(self, screen, w, h):
        self.screen = screen
        self.w = w
        self.h = h
        self.action = None

        self.backdrop = theme.StarField(w, h)
        self.settings = load_settings()

        self.panel = pygame.Rect(180, 100, 440, 400)
        p = self.panel

        self.back_btn = pygame.Rect(p.x + 14, p.y + 14, 44, 40)
        self.menu_btn = pygame.Rect(p.centerx - 110, p.bottom - 62, 220, 44)

        self.rows = {
            "music_enabled": (p.y + 104, "music"),
            "sound_enabled": (p.y + 166, "speaker"),
            "sound_volume": (p.y + 234, "speaker"),
            "mobile_controls": (p.y + 302, "pad"),
        }

        self.labels = {
            "music_enabled": "MUSIC",
            "sound_enabled": "SOUND EFFECTS",
            "sound_volume": "VOLUME",
            "mobile_controls": "MOBILE CONTROLS",
        }

        self.toggles = {}

        for key, (y, _icon) in self.rows.items():
            if key != "sound_volume":
                self.toggles[key] = pygame.Rect(p.right - 92, y - 14, 56, 28)

        vy = self.rows["sound_volume"][0]
        self.slider = pygame.Rect(p.x + 96, vy + 8, 200, 12)
        self.dragging = False

    def commit(self):
        save_settings(self.settings)
        audio.apply(self.settings)

    def set_volume(self, x):
        value = round((x - self.slider.x) / self.slider.w * 100)
        self.settings["sound_volume"] = max(0, min(100, value))
        audio.apply(self.settings)

    def handle_events(self, events):
        self.action = None

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.click(event.pos)

            elif event.type == pygame.MOUSEMOTION and self.dragging:
                self.set_volume(event.pos[0])

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.dragging:
                    self.dragging = False
                    self.commit()

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.action = "back"

    def click(self, pos):
        if self.back_btn.collidepoint(pos) or self.menu_btn.collidepoint(pos):
            audio.play_click()
            self.action = "back"
            return

        for key, rect in self.toggles.items():
            if rect.inflate(20, 20).collidepoint(pos):
                self.settings[key] = not self.settings.get(key, False)
                self.commit()
                audio.play_click()
                return

        if self.slider.inflate(24, 30).collidepoint(pos):
            self.dragging = True
            self.set_volume(pos[0])

    def draw_row_box(self, y, tall=False):
        p = self.panel
        height = 66 if tall else 52
        top = y - height // 2 - (6 if tall else 0)

        theme.panel(
            self.screen,
            pygame.Rect(p.x + 20, top, p.w - 40, height),
            border=(84, 62, 170),
            fill=theme.FIELD,
            glow=False,
            cut=8,
            thin=True,
        )

    def draw_row_icon(self, name, y, color):
        box = pygame.Rect(0, 0, 36, 36)
        box.center = (self.panel.x + 52, y)

        theme.panel(
            self.screen, box, border=theme.BORDER, fill=theme.PANEL,
            glow=False, cut=7, thin=True,
        )
        theme.icon(self.screen, name, box.centerx, box.centery, color, 0.9)

    def draw(self):
        s = self.screen
        mouse = pygame.mouse.get_pos()
        p = self.panel

        self.backdrop.draw(s)
        theme.panel(s, p, thin=True, cut=14)

        theme.button(s, self.back_btn, "", mouse, icon_name="back")

        title = theme.glow_text(
            s, "SETTINGS", 28, theme.TEXT, theme.BTN, (p.centerx + 24, p.y + 36)
        )
        theme.icon(s, "gear", title.left - 28, p.y + 36, theme.LAVENDER, 1.3)

        pygame.draw.line(
            s, theme.BORDER, (p.x + 28, p.y + 66), (p.right - 28, p.y + 66), 1
        )

        for key, (y, icon_name) in self.rows.items():
            if key in self.toggles:
                on = bool(self.settings.get(key, False))

                if key == "sound_enabled":
                    icon_name = "speaker" if on else "speaker_off"

                self.draw_row_box(y)
                self.draw_row_icon(
                    icon_name, y, theme.LAVENDER if on else theme.TEXT_DIM
                )
                theme.text(
                    s,
                    self.labels[key],
                    16,
                    theme.TEXT if on else theme.TEXT_DIM,
                    (p.x + 84, y),
                    anchor="midleft",
                )
                theme.switch(s, self.toggles[key], on)
            else:
                volume = self.settings.get("sound_volume", 50)

                self.draw_row_box(y, tall=True)
                self.draw_row_icon("speaker", y - 6, theme.LAVENDER)
                theme.text(
                    s,
                    self.labels[key],
                    16,
                    theme.TEXT,
                    (p.x + 84, y - 18),
                    anchor="midleft",
                )

                frac = volume / 100.0
                theme.bar(s, self.slider, frac, theme.ACCENT)

                knob_x = self.slider.x + int(self.slider.w * frac)
                pygame.draw.circle(
                    s, theme.TEXT, (knob_x, self.slider.centery), 10
                )
                pygame.draw.circle(
                    s, theme.BORDER_HI, (knob_x, self.slider.centery), 10, 2
                )

                theme.text(
                    s,
                    f"{volume}%",
                    15,
                    theme.TEXT,
                    (self.slider.right + 14, self.slider.centery),
                    anchor="midleft",
                )

        theme.button(
            s, self.menu_btn, "BACK TO MENU", mouse,
            icon_name="back", primary=True, size=17,
        )