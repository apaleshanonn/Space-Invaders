import pygame

import theme
from db import get_player_highest_score, get_player_rank, load_leaderboard
from sound import audio

ROW_X = 140
ROW_W = 520
RANK_X = ROW_X + 45
NAME_X = ROW_X + 95
SCORE_X = ROW_X + 330
LEVEL_X = ROW_X + 470


class Leader:
    def __init__(self, screen, w, h, player=None):
        self.screen = screen
        self.w = w
        self.h = h
        self.player = player
        self.action = None

        self.backdrop = theme.StarField(w, h)
        self.back_btn = pygame.Rect(16, 16, 48, 44)
        self.card = pygame.Rect(120, 64, 560, 462)

        self.player_id = None

        if isinstance(player, dict):
            self.player_id = player.get("player_id")

        self.rows = load_leaderboard()
        self.me_rank = None
        self.me_best = 0
        self.me_level = 0

        if self.player_id is not None:
            self.me_rank = get_player_rank(self.player_id)
            self.me_best = get_player_highest_score(self.player_id)

            for row in self.rows:
                if row.get("player_id") == self.player_id:
                    self.me_level = row.get("level", 1)

    def username(self):
        if isinstance(self.player, dict):
            return str(self.player.get("username", "YOU"))

        return "YOU"

    def draw_row(self, y, rank, name, score, level, highlight):
        s = self.screen
        rect = pygame.Rect(ROW_X, y, ROW_W, 26)

        if highlight:
            theme.panel(
                s, rect, border=theme.BORDER_HI, fill=(92, 56, 210),
                glow=False, cut=7, thin=True,
            )
        else:
            pygame.draw.rect(s, theme.FIELD, rect, border_radius=6)
            pygame.draw.rect(s, (70, 50, 150), rect, 1, border_radius=6)

        crowns = {1: theme.GOLD, 2: theme.SILVER, 3: theme.BRONZE}

        if rank in crowns:
            theme.icon(s, "crown", RANK_X, rect.centery, crowns[rank], 0.9)
        else:
            theme.text(
                s, rank, 16, theme.TEXT, (RANK_X, rect.centery), anchor="center"
            )

        theme.text(
            s, name, 16, theme.TEXT, (NAME_X, rect.centery), anchor="midleft"
        )
        theme.text(
            s,
            score,
            16,
            theme.GOLD if rank == 1 else theme.TEXT,
            (SCORE_X, rect.centery),
            anchor="center",
        )
        theme.text(
            s, level, 16, theme.TEXT, (LEVEL_X, rect.centery), anchor="center"
        )

    def draw(self):
        s = self.screen
        mouse = pygame.mouse.get_pos()
        card = self.card

        self.backdrop.draw(s)

        theme.button(s, self.back_btn, "", mouse, icon_name="back")
        theme.panel(s, card, thin=True, cut=14)

        title = theme.glow_text(
            s, "LEADERBOARD", 28, theme.TEXT, theme.BTN,
            (card.centerx + 20, card.y + 32),
        )
        theme.icon(s, "trophy", title.left - 28, card.y + 32, theme.GOLD, 1.3)

        header = pygame.Rect(ROW_X, card.y + 58, ROW_W, 28)
        theme.panel(
            s, header, border=theme.BORDER, fill=theme.PANEL_HOVER,
            glow=False, cut=7, thin=True,
        )

        cy = header.centery
        theme.text(s, "RANK", 14, theme.LAVENDER, (RANK_X, cy), anchor="center")
        theme.text(s, "PLAYER", 14, theme.LAVENDER, (NAME_X, cy), anchor="midleft")
        theme.text(s, "SCORE", 14, theme.LAVENDER, (SCORE_X, cy), anchor="center")
        theme.text(s, "LEVEL", 14, theme.LAVENDER, (LEVEL_X, cy), anchor="center")

        if not self.rows:
            theme.icon(s, "trophy", card.centerx, 270, theme.TEXT_DIM, 3.0)
            theme.text(
                s,
                "NO SCORES YET",
                20,
                theme.TEXT_DIM,
                (card.centerx, 340),
                anchor="center",
            )
            return

        in_top = False

        for index, row in enumerate(self.rows[:10], start=1):
            mine = row.get("player_id") == self.player_id

            if mine:
                in_top = True

            self.draw_row(
                card.y + 96 + (index - 1) * 30,
                index,
                row.get("username", "PLAYER"),
                row.get("score", 0),
                row.get("level", 1),
                mine,
            )

        if not in_top and self.me_rank and self.me_best > 0:
            theme.text(
                s, "...", 18, theme.TEXT_DIM,
                (card.centerx, card.y + 404), anchor="center",
            )
            self.draw_row(
                card.y + 418,
                self.me_rank,
                self.username(),
                self.me_best,
                self.me_level or 1,
                True,
            )

    def handle_events(self, events):
        self.action = None

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.back_btn.collidepoint(event.pos):
                    audio.play_click()
                    self.action = "back"

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.action = "back"