import pygame

import theme
from db import delete_player, get_player_rank, get_player_stats, update_username
from entities.player import SHIP_COUNT, get_ship_image
from player_prefs import delete_prefs, get_prefs, set_prefs
from sound import audio

USERNAME_MIN = 3
USERNAME_MAX = 16
AVATAR_COUNT = 4


class Profile:
    def __init__(self, screen, w, h, player=None):
        self.screen = screen
        self.w = w
        self.h = h
        self.action = None

        if isinstance(player, dict):
            self.player = dict(player)
        else:
            self.player = {"player_id": None, "username": str(player or "PLAYER")}

        self.backdrop = theme.StarField(w, h)

        c = pygame.Rect(150, 92, 500, 412)
        self.card = c

        self.back_btn = pygame.Rect(16, 16, 48, 44)
        self.tab = pygame.Rect(c.centerx - 115, c.y - 20, 230, 38)

        self.avatar_center = (c.x + 58, c.y + 60)
        self.name_box = pygame.Rect(c.x + 104, c.y + 24, 218, 72)
        self.edit_rect = pygame.Rect(
            self.name_box.x + 8, self.name_box.y + 28, self.name_box.w - 16, 36
        )
        self.ship_box = pygame.Rect(c.x + 334, c.y + 24, 146, 72)

        self.stat_rects = [
            pygame.Rect(c.x + 20 + i * 118, c.y + 108, 106, 50) for i in range(4)
        ]

        self.ship_panel = pygame.Rect(c.x + 20, c.y + 168, 460, 84)
        self.avatar_panel = pygame.Rect(c.x + 20, c.y + 262, 460, 84)

        self.ship_slots = [
            pygame.Rect(self.ship_panel.x + 16 + i * 110, self.ship_panel.y + 28, 98, 46)
            for i in range(SHIP_COUNT)
        ]
        self.avatar_slots = [
            pygame.Rect(self.avatar_panel.x + 16 + i * 110, self.avatar_panel.y + 28, 98, 46)
            for i in range(AVATAR_COUNT)
        ]

        self.bottom_back = pygame.Rect(c.x + 20, c.bottom - 52, 130, 40)
        self.save_btn = pygame.Rect(c.right - 150, c.bottom - 52, 130, 40)
        self.delete_btn = pygame.Rect(c.centerx - 22, c.bottom - 52, 44, 40)

        dialog = pygame.Rect(0, 0, 320, 230)
        dialog.center = (w // 2, h // 2)
        self.dialog = dialog
        self.yes_btn = pygame.Rect(dialog.x + 44, dialog.bottom - 72, 100, 48)
        self.no_btn = pygame.Rect(dialog.right - 144, dialog.bottom - 72, 100, 48)

        self.dim = pygame.Surface((w, h), pygame.SRCALPHA)
        self.dim.fill((8, 5, 22, 190))

        self.editing = False
        self.edit_value = ""
        self.confirm_delete = False

        self.message = ""
        self.message_timer = 0

        self.stats = {"highest": 0, "games": 0, "total": 0, "level": 0}
        self.rank = None

        pid = self.player.get("player_id")
        prefs = get_prefs(pid)
        self.ship_sel = prefs["ship"]
        self.avatar_sel = prefs["avatar"]

        if pid is not None:
            self.stats = get_player_stats(pid)
            self.rank = get_player_rank(pid)

    def say(self, message):
        self.message = message
        self.message_timer = 180

    def start_edit(self):
        self.editing = True
        self.edit_value = str(self.player.get("username", ""))

    def save(self):
        pid = self.player.get("player_id")

        if self.editing:
            value = self.edit_value.strip()

            if len(value) < USERNAME_MIN:
                self.say("USERNAME TOO SHORT")
                return

            if value != self.player.get("username"):
                ok, message = update_username(pid, value)

                if not ok:
                    self.say(message)
                    return

                self.player["username"] = value

            self.editing = False

        set_prefs(pid, ship=self.ship_sel, avatar=self.avatar_sel)
        self.say("PROFILE SAVED")

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.click(event.pos)

            elif event.type == pygame.KEYDOWN and self.editing:
                self.key(event)

    def key(self, event):
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.save()

        elif event.key == pygame.K_ESCAPE:
            self.editing = False

        elif event.key == pygame.K_BACKSPACE:
            self.edit_value = self.edit_value[:-1]

        else:
            ch = event.unicode

            if (
                ch
                and ch.isascii()
                and (ch.isalnum() or ch in "_.")
                and len(self.edit_value) < USERNAME_MAX
            ):
                self.edit_value += ch

    def click(self, pos):
        if self.confirm_delete:
            if self.yes_btn.collidepoint(pos):
                audio.play_click()

                pid = self.player.get("player_id")

                if delete_player(pid):
                    delete_prefs(pid)
                    self.action = "deleted"
                else:
                    self.confirm_delete = False
                    self.say("DATABASE ERROR")

            elif self.no_btn.collidepoint(pos):
                audio.play_click()
                self.confirm_delete = False

            return

        if self.back_btn.collidepoint(pos) or self.bottom_back.collidepoint(pos):
            audio.play_click()
            self.action = "back"
            return

        if self.save_btn.collidepoint(pos):
            audio.play_click()
            self.save()
            return

        if self.delete_btn.collidepoint(pos):
            audio.play_click()
            self.confirm_delete = True
            return

        if self.edit_rect.collidepoint(pos):
            if not self.editing:
                audio.play_click()
                self.start_edit()

            return

        for i, rect in enumerate(self.ship_slots):
            if rect.collidepoint(pos):
                audio.play_click()
                self.ship_sel = i
                return

        for i, rect in enumerate(self.avatar_slots):
            if rect.collidepoint(pos):
                audio.play_click()
                self.avatar_sel = i
                return

    def draw_section(self, rect, label):
        theme.panel(
            self.screen, rect, border=(84, 62, 170), fill=theme.FIELD,
            glow=False, cut=8, thin=True,
        )
        theme.text(
            self.screen, label, 12, theme.LAVENDER,
            (rect.x + 16, rect.y + 17), anchor="midleft",
        )

    def draw_stat(self, rect, label, value):
        s = self.screen

        theme.panel(
            s, rect, border=(84, 62, 170), fill=theme.FIELD, glow=False, cut=8,
            thin=True,
        )
        theme.text(
            s, label, 11, theme.TEXT_DIM,
            (rect.centerx, rect.y + 14), anchor="center",
        )
        theme.text(
            s, value, 22, theme.TEXT,
            (rect.centerx, rect.y + 34), anchor="center",
        )

    def draw_slot(self, rect, selected, mouse):
        hover = rect.collidepoint(mouse)

        theme.panel(
            self.screen,
            rect,
            border=theme.BORDER_HI if selected else (theme.BORDER if hover else (84, 62, 170)),
            fill=(46, 30, 114) if selected else theme.PANEL,
            glow=selected,
            cut=8,
            thin=True,
        )

    def draw(self):
        s = self.screen
        mouse = pygame.mouse.get_pos()
        card = self.card

        self.backdrop.draw(s)

        theme.button(s, self.back_btn, "", mouse, icon_name="back")
        theme.panel(s, card, thin=True, cut=14)

        theme.panel(
            s, self.tab, border=theme.BORDER_HI, fill=theme.PANEL_HOVER,
            cut=10, thin=True,
        )
        title = theme.text(
            s, "PLAYER PROFILE", 18, theme.TEXT,
            (self.tab.centerx + 16, self.tab.centery), anchor="center",
        )
        theme.icon(s, "user", title.left - 22, self.tab.centery, theme.LAVENDER, 1.2)

        ax, ay = self.avatar_center
        pygame.draw.circle(s, theme.BORDER, (ax, ay), 41, 2)
        theme.draw_avatar(s, (ax, ay), 36, self.avatar_sel)

        self.draw_section(self.name_box, "PLAYER NAME")

        hover_name = self.edit_rect.collidepoint(mouse)
        theme.panel(
            s,
            self.edit_rect,
            border=theme.BORDER_HI if (self.editing or hover_name) else theme.BORDER,
            fill=theme.FIELD,
            glow=self.editing,
            cut=8,
            thin=True,
        )
        theme.icon(
            s, "user", self.edit_rect.x + 22, self.edit_rect.centery,
            theme.LAVENDER, 0.9,
        )

        if self.editing:
            r = theme.text(
                s, self.edit_value, 20, theme.TEXT,
                (self.edit_rect.x + 44, self.edit_rect.centery),
                anchor="midleft", bold=False,
            )

            if (pygame.time.get_ticks() // 500) % 2 == 0:
                pygame.draw.line(
                    s, theme.LAVENDER,
                    (r.right + 3, self.edit_rect.centery - 12),
                    (r.right + 3, self.edit_rect.centery + 12),
                    2,
                )
        else:
            theme.text(
                s, str(self.player.get("username", "PLAYER")), 20, theme.TEXT,
                (self.edit_rect.x + 44, self.edit_rect.centery), anchor="midleft",
            )

        theme.icon(
            s, "pencil", self.edit_rect.right - 22, self.edit_rect.centery,
            theme.BORDER_HI if hover_name else theme.LAVENDER, 0.9,
        )

        self.draw_section(self.ship_box, "SELECTED SHIP")
        preview = get_ship_image(self.ship_sel, 40, 40)
        s.blit(
            preview,
            preview.get_rect(center=(self.ship_box.centerx, self.ship_box.y + 48)),
        )

        rank_text = f"#{self.rank}" if self.rank else "-"

        for rect, (label, value) in zip(
            self.stat_rects,
            (
                ("TOTAL SCORE", self.stats["total"]),
                ("BEST SCORE", self.stats["highest"]),
                ("HIGHEST LEVEL", self.stats["level"]),
                ("RANK", rank_text),
            ),
        ):
            self.draw_stat(rect, label, value)

        self.draw_section(self.ship_panel, "CHOOSE YOUR SHIP")

        for i, rect in enumerate(self.ship_slots):
            self.draw_slot(rect, i == self.ship_sel, mouse)
            img = get_ship_image(i, 40, 40)
            s.blit(img, img.get_rect(center=rect.center))

        self.draw_section(self.avatar_panel, "CHOOSE AVATAR")

        for i, rect in enumerate(self.avatar_slots):
            self.draw_slot(rect, i == self.avatar_sel, mouse)
            theme.draw_avatar(s, rect.center, 22, i)

        theme.button(s, self.bottom_back, "BACK", mouse, icon_name="back", size=17)
        theme.button(
            s, self.save_btn, "SAVE", mouse, icon_name="save",
            primary=True, size=17,
        )
        theme.button(s, self.delete_btn, "", mouse, icon_name="trash", danger=True)

        if self.message_timer > 0:
            self.message_timer -= 1
            theme.text(
                s, self.message, 17, theme.LAVENDER,
                (card.centerx, card.bottom + 24), anchor="center",
            )

        if self.confirm_delete:
            s.blit(self.dim, (0, 0))
            theme.panel(s, self.dialog, border=theme.BAD)
            theme.icon(
                s, "trash", self.dialog.centerx, self.dialog.y + 62, theme.BAD, 2.6
            )
            theme.text(
                s,
                "DELETE ACCOUNT?",
                20,
                theme.TEXT,
                (self.dialog.centerx, self.dialog.y + 120),
                anchor="center",
            )
            theme.button(s, self.yes_btn, "", mouse, icon_name="check", danger=True)
            theme.button(s, self.no_btn, "", mouse, icon_name="cross", primary=True)