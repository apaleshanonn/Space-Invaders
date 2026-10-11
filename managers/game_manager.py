import math
import random

import pygame

import theme
from db import get_player_highest_score, save_score
from entities.boss import Boss
from entities.bullet import Bullet
from entities.button import MobileButtons
from entities.enemy import Enemy
from entities.player import Player
from entities.powerup import COLORS, ICONS, KINDS, WEIGHTS, PowerUp
from managers.settings import SettingsScreen
from player_prefs import get_prefs
from settings_manager import load_settings
from sound import audio

POWER_TIME = 480
COMBO_TIME = 150
COMBO_STEP = 5
MAX_MULT = 5
DROP_CHANCE = 0.14


class GameManager:
    def __init__(self, screen, w, h):
        self.screen = screen
        self.w = w
        self.h = h

        self.canvas = pygame.Surface((w, h))
        self.backdrop = theme.StarField(w, h)

        self.dim = pygame.Surface((w, h), pygame.SRCALPHA)
        self.dim.fill((8, 5, 22, 175))

        self.current_player_id = None
        self.player_name = "PLAYER"
        self.game_state = "playing"

        self.pause_btn = pygame.Rect(w - 46, 6, 38, 38)
        self.settings_screen = None

        self.start_again()

    def start_again(self):
        self.reload_settings()

        ship = get_prefs(self.current_player_id)["ship"]
        self.player = Player(self.w, self.h, ship)

        self.bullets = []
        self.enemies = []
        self.shots = []
        self.powerups = []
        self.particles = []
        self.boss = None

        self.score = 0
        self.lives = 3
        self.level = 1

        self.combo = 0
        self.combo_timer = 0
        self.multiplier = 1

        self.fire_cd = 0
        self.rapid_t = 0
        self.triple_t = 0
        self.shake = 0

        self.score_saved = False
        self.new_best = False
        self.best_score = 0

        if self.current_player_id is not None:
            self.best_score = get_player_highest_score(self.current_player_id)

        self.start_wave()
        self.game_state = "playing"

    def reload_settings(self):
        self.settings = load_settings()
        self.mobile = MobileButtons() if self.settings.get("mobile_controls") else None

    def start_wave(self):
        self.shots = []

        if self.level % 5 == 0:
            self.boss = Boss(self.level, self.w)
            self.enemies = []
        else:
            self.boss = None

            count = min(4 + self.level, 8)
            speed = min(3 + self.level * 0.35, 7)

            self.enemies = [
                Enemy(
                    i,
                    count,
                    self.w,
                    speed=speed,
                    hp=2 if (self.level >= 6 and i % 3 == 0) else 1,
                )
                for i in range(count)
            ]

        self.drop_interval = max(28, 110 - self.level * 7)
        self.drop_timer = self.drop_interval

    def finish_session(self):
        if (
            not self.score_saved
            and self.score > 0
            and self.current_player_id is not None
        ):
            save_score(self.current_player_id, self.score, self.level)
            self.score_saved = True

    def leave_to_home(self):
        self.finish_session()
        self.game_state = "back_home"

    def game_over(self):
        self.new_best = self.score > self.best_score and self.score > 0
        self.finish_session()
        self.game_state = "game_over"

    def update(self, events):
        if self.game_state == "settings":
            if self.settings_screen is None:
                self.game_state = "paused"
                return

            self.settings_screen.handle_events(events)

            if self.settings_screen.action == "back":
                self.settings_screen = None
                self.reload_settings()
                self.game_state = "paused"

            return

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_p, pygame.K_ESCAPE):
                    if self.game_state == "playing":
                        self.game_state = "paused"
                    elif self.game_state == "paused":
                        self.game_state = "playing"

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_click(event.pos)

        if self.shake > 0:
            self.shake -= 1

        if self.game_state == "playing":
            self.update_play(events)

    def pause_rects(self):
        panel = pygame.Rect(0, 0, 380, 344)
        panel.center = (self.w // 2, self.h // 2)
        resume = pygame.Rect(panel.x + 50, panel.y + 134, 280, 52)
        menu = pygame.Rect(panel.x + 50, panel.y + 198, 280, 52)
        settings = pygame.Rect(panel.x + 50, panel.y + 262, 280, 52)
        return panel, resume, menu, settings

    def over_rects(self):
        panel = pygame.Rect(0, 0, 360, 396)
        panel.center = (self.w // 2, self.h // 2)
        again = pygame.Rect(panel.x + 30, panel.y + 270, 300, 46)
        menu = pygame.Rect(panel.x + 30, panel.y + 326, 300, 46)
        return panel, again, menu

    def handle_click(self, pos):
        if self.game_state == "playing":
            if self.pause_btn.collidepoint(pos):
                audio.play_click()
                self.game_state = "paused"

        elif self.game_state == "paused":
            _panel, resume, menu, settings = self.pause_rects()

            if resume.collidepoint(pos):
                audio.play_click()
                self.game_state = "playing"
            elif menu.collidepoint(pos):
                audio.play_click()
                self.leave_to_home()
            elif settings.collidepoint(pos):
                audio.play_click()
                self.settings_screen = SettingsScreen(self.screen, self.w, self.h)
                self.game_state = "settings"

        elif self.game_state == "game_over":
            _panel, again, menu = self.over_rects()

            if again.collidepoint(pos):
                audio.play_click()
                self.start_again()
            elif menu.collidepoint(pos):
                audio.play_click()
                self.leave_to_home()

    def shoot(self):
        px = self.player.x + self.player.width / 2 - 16
        py = self.player.y - 10

        self.bullets.append(Bullet(px, py))

        if self.triple_t > 0:
            self.bullets.append(Bullet(px - 14, py + 8, dx=-2.5))
            self.bullets.append(Bullet(px + 14, py + 8, dx=2.5))

        self.fire_cd = 6 if self.rapid_t > 0 else 14

    def update_play(self, events):
        keys = pygame.key.get_pressed()

        self.player.update()

        want_fire = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]

        if self.mobile and self.mobile.handle_mouse(self.player, events):
            want_fire = True

        if self.fire_cd > 0:
            self.fire_cd -= 1

        if want_fire and self.fire_cd <= 0 and not self.player.is_blinking:
            self.shoot()

        if self.rapid_t > 0:
            self.rapid_t -= 1

        if self.triple_t > 0:
            self.triple_t -= 1

        for bullet in self.bullets:
            bullet.update()

        for enemy in self.enemies:
            enemy.update()

        self.update_enemy_drops()

        if self.boss and self.boss.active:
            self.shots.extend(self.boss.update())

        for shot in self.shots:
            shot.update()

        for power in self.powerups:
            power.update()

        self.bullet_collisions()
        self.player_collisions()
        self.collect_powerups()

        self.bullets = [b for b in self.bullets if b.is_active]
        self.shots = [s for s in self.shots if s.active]
        self.powerups = [p for p in self.powerups if p.active]

        if self.combo_timer > 0:
            self.combo_timer -= 1

            if self.combo_timer == 0:
                self.combo = 0
                self.multiplier = 1

        self.update_particles()

        if self.game_state == "playing":
            if self.boss:
                cleared = not self.boss.active
            else:
                cleared = not any(e.active for e in self.enemies)

            if cleared:
                self.next_wave()

    def update_enemy_drops(self):
        self.drop_timer -= 1

        if self.drop_timer > 0:
            return

        waiting = [
            e for e in self.enemies if e.active and e.state == "waiting"
        ]

        if waiting:
            amount = 1 + (1 if self.level >= 4 else 0) + (1 if self.level >= 8 else 0)

            for enemy in random.sample(waiting, min(amount, len(waiting))):
                target_x = self.player.x + self.player.width // 2 - enemy.width // 2
                enemy.start_drop(target_x, self.player.y)

        self.drop_timer = self.drop_interval + random.randint(0, 20)

    def register_hit(self):
        audio.play_hit()

        self.combo += 1
        self.combo_timer = COMBO_TIME
        self.multiplier = min(MAX_MULT, 1 + self.combo // COMBO_STEP)

    def bullet_collisions(self):
        for bullet in self.bullets:
            if not bullet.is_active:
                continue

            rect = bullet.get_rect()

            if (
                self.boss
                and self.boss.active
                and rect.colliderect(self.boss.get_rect())
            ):
                bullet.is_active = False
                self.register_hit()
                self.score += 1 * self.multiplier
                self.burst(rect.centerx, rect.top, theme.ACCENT, 5, 3)
                self.shake = max(self.shake, 3)

                if self.boss.hit(1):
                    self.boss_down()

                continue

            for enemy in self.enemies:
                if enemy.active and rect.colliderect(enemy.get_rect()):
                    bullet.is_active = False
                    self.register_hit()
                    enemy.hp -= 1

                    if enemy.hp <= 0:
                        self.kill_enemy(enemy)
                    else:
                        self.burst(rect.centerx, rect.top, theme.LAVENDER, 6, 3)

                    break

    def kill_enemy(self, enemy):
        enemy.active = False
        self.score += 1 * self.multiplier

        cx, cy = enemy.get_rect().center
        self.burst(cx, cy, theme.INVADER_COLORS[enemy.index % 5], 16, 5)

        if random.random() < DROP_CHANCE:
            weights = list(WEIGHTS)

            if self.lives >= 5:
                weights[KINDS.index("life")] = 0

            kind = random.choices(KINDS, weights=weights)[0]
            self.powerups.append(PowerUp(kind, cx, cy))

    def boss_down(self):
        self.score += 10 + 2 * self.level

        cx, cy = self.boss.get_rect().center
        self.burst(cx, cy, theme.ACCENT, 40, 7)
        self.burst(cx, cy, theme.BORDER_HI, 30, 5)
        self.shake = 24
        self.shots = []

    def player_collisions(self):
        player_rect = self.player.get_rect().inflate(-30, -30)

        for enemy in self.enemies:
            if enemy.active and player_rect.colliderect(
                enemy.get_rect().inflate(-20, -20)
            ):
                enemy.active = False
                cx, cy = enemy.get_rect().center
                self.burst(cx, cy, theme.BAD, 14, 5)
                self.player_hit()

        for shot in self.shots:
            if shot.active and player_rect.colliderect(shot.get_rect()):
                shot.active = False
                self.player_hit()

        if (
            self.boss
            and self.boss.active
            and player_rect.colliderect(self.boss.get_rect())
        ):
            self.player_hit()

    def player_hit(self):
        if self.game_state != "playing":
            return

        if self.player.is_blinking or self.player.invuln > 0:
            return

        cx, cy = self.player.get_rect().center

        if self.player.shield:
            self.player.shield = False
            self.player.invuln = 40
            self.burst(cx, cy, theme.ICE, 20, 5)
            self.shake = 8
            return

        self.lives -= 1
        self.combo = 0
        self.combo_timer = 0
        self.multiplier = 1
        self.shake = 16
        self.burst(cx, cy, theme.BAD, 24, 6)
        self.player.start_blink()

        if self.lives <= 0:
            self.lives = 0
            self.game_over()

    def collect_powerups(self):
        player_rect = self.player.get_rect()

        for power in self.powerups:
            if not power.active or not player_rect.colliderect(power.get_rect()):
                continue

            power.active = False
            self.burst(int(power.x), int(power.y), COLORS[power.kind], 12, 4)

            if power.kind == "shield":
                self.player.shield = True
            elif power.kind == "rapid":
                self.rapid_t = POWER_TIME
            elif power.kind == "triple":
                self.triple_t = POWER_TIME
            elif power.kind == "life":
                self.lives = min(5, self.lives + 1)

    def next_wave(self):
        self.level += 1
        self.bullets = []
        self.powerups = []
        self.start_wave()
        self.game_state = "playing"

    def burst(self, x, y, color, count=14, speed=4):
        for _ in range(count):
            angle = random.random() * 6.283
            velocity = random.random() * speed + 1

            self.particles.append(
                [
                    x,
                    y,
                    math.cos(angle) * velocity,
                    math.sin(angle) * velocity,
                    random.randint(18, 34),
                    color,
                ]
            )

        if len(self.particles) > 300:
            self.particles = self.particles[-300:]

    def update_particles(self):
        for p in self.particles:
            p[0] += p[2]
            p[1] += p[3]
            p[4] -= 1

        self.particles = [p for p in self.particles if p[4] > 0]

    def draw_hud(self, c):
        mouse = pygame.mouse.get_pos()

        theme.icon(c, "heart", 30, 24, theme.BAD, 1.3)
        theme.text(
            c, f"x{self.lives}", 20, theme.TEXT, (50, 24), anchor="midleft"
        )

        score_rect = pygame.Rect(self.w - 304, 8, 146, 32)
        level_rect = pygame.Rect(self.w - 156, 8, 100, 32)

        for rect, label, color in (
            (score_rect, f"SCORE: {self.score}", theme.TEXT),
            (level_rect, f"LEVEL: {self.level}", theme.LAVENDER),
        ):
            theme.panel(
                c, rect, border=theme.BORDER_HI, fill=theme.PANEL,
                glow=False, cut=10,
            )
            theme.text(c, label, 15, color, rect.center, anchor="center")

        theme.button(c, self.pause_btn, "", mouse, icon_name="pause")

        if self.combo > 0:
            if self.multiplier >= MAX_MULT:
                frac = 1.0
            else:
                frac = (self.combo % COMBO_STEP) / COMBO_STEP

            theme.bar(
                c,
                pygame.Rect(self.w - 156, 50, 100, 8),
                frac,
                theme.GOLD,
            )

            if self.multiplier > 1:
                theme.text(
                    c,
                    f"x{self.multiplier}",
                    14,
                    theme.GOLD,
                    (self.w - 46, 54),
                    anchor="midleft",
                )

        if self.boss and self.boss.active:
            box = pygame.Rect(self.w // 2 - 120, 46, 200, 24)
            theme.panel(
                c, box, border=theme.BAD, fill=theme.PANEL, glow=False, cut=8
            )
            theme.text(
                c,
                "BOSS",
                12,
                theme.BAD,
                (box.x + 12, box.centery),
                anchor="midleft",
            )
            theme.bar(
                c,
                pygame.Rect(box.x + 56, box.centery - 4, box.w - 70, 8),
                self.boss.hp / self.boss.max_hp,
                theme.BAD,
            )

        active = []

        if self.player.shield:
            active.append(("shield", 1.0))

        if self.rapid_t > 0:
            active.append(("rapid", self.rapid_t / POWER_TIME))

        if self.triple_t > 0:
            active.append(("triple", self.triple_t / POWER_TIME))

        for i, (kind, frac) in enumerate(active):
            x = 34 + i * 48
            y = 84
            color = COLORS[kind]

            pygame.draw.circle(c, theme.FIELD, (x, y), 17)
            pygame.draw.circle(c, color, (x, y), 17, 2)
            theme.icon(c, ICONS[kind], x, y, color, 0.8)
            theme.bar(c, pygame.Rect(x - 16, y + 22, 32, 6), frac, color)

    def draw_particles(self, c):
        for x, y, _vx, _vy, life, color in self.particles:
            pygame.draw.circle(c, color, (int(x), int(y)), max(1, life // 8))

    def draw(self):
        if self.game_state == "settings" and self.settings_screen is not None:
            self.settings_screen.draw()
            return

        c = self.canvas

        self.backdrop.draw(c)

        for power in self.powerups:
            power.draw(c)

        for enemy in self.enemies:
            enemy.draw(c)

        if self.boss:
            self.boss.draw(c)

        for shot in self.shots:
            shot.draw(c)

        for bullet in self.bullets:
            bullet.draw(c)

        self.player.draw(c)
        self.draw_particles(c)
        self.draw_hud(c)

        if self.mobile:
            self.mobile.draw(c)

        ox = oy = 0

        if self.shake > 0:
            amp = min(8, self.shake // 2 + 1)
            ox = random.randint(-amp, amp)
            oy = random.randint(-amp, amp)
            self.screen.fill(theme.BG)

        self.screen.blit(c, (ox, oy))

        if self.game_state == "paused":
            self.draw_pause()
        elif self.game_state == "game_over":
            self.draw_over()

    def draw_pause(self):
        s = self.screen
        mouse = pygame.mouse.get_pos()
        panel, resume, menu, settings = self.pause_rects()

        s.blit(self.dim, (0, 0))
        theme.panel(s, panel)

        badge = (panel.x + 82, panel.y + 52)
        pygame.draw.circle(s, theme.LAVENDER, badge, 21, 3)
        theme.icon(s, "pause", badge[0], badge[1], theme.TEXT, 1.2)
        theme.glow_text(
            s, "GAME PAUSED", 28, theme.TEXT, theme.BTN,
            (panel.centerx + 36, panel.y + 52),
        )

        ly = panel.y + 100
        theme.text(s, "OPTIONS", 15, theme.TEXT, (panel.centerx, ly), anchor="center")
        pygame.draw.line(s, theme.BORDER, (panel.x + 40, ly), (panel.centerx - 54, ly), 2)
        pygame.draw.line(s, theme.BORDER, (panel.centerx + 54, ly), (panel.right - 40, ly), 2)

        theme.button(s, resume, "RESUME", mouse, icon_name="play", size=19, align="left")
        theme.button(s, menu, "MAIN MENU", mouse, icon_name="home", size=19, align="left")
        theme.button(s, settings, "SETTINGS", mouse, icon_name="gear", size=19, align="left")

    def draw_over(self):
        s = self.screen
        mouse = pygame.mouse.get_pos()
        panel, again, menu = self.over_rects()

        s.blit(self.dim, (0, 0))
        theme.panel(s, panel)

        title = theme.glow_text(
            s, "GAME OVER", 32, theme.TEXT, theme.BTN,
            (panel.centerx + 26, panel.y + 46),
        )
        theme.icon(s, "skull", title.left - 30, panel.y + 46, theme.TEXT, 1.9)

        box = pygame.Rect(panel.x + 30, panel.y + 86, 300, 166)
        theme.panel(
            s, box, border=theme.BORDER, fill=theme.FIELD, glow=False, cut=12
        )

        theme.text(s, "SCORE", 13, theme.TEXT_DIM, (box.centerx, box.y + 20), anchor="center")
        theme.text(s, self.score, 44, theme.TEXT, (box.centerx, box.y + 54), anchor="center")

        if self.new_best:
            theme.icon(s, "crown", box.centerx - 56, box.y + 88, theme.GOLD, 0.9)
            theme.text(
                s, "NEW BEST", 16, theme.GOLD,
                (box.centerx - 36, box.y + 88), anchor="midleft",
            )
        else:
            pygame.draw.line(
                s, theme.BORDER, (box.x + 30, box.y + 88), (box.right - 30, box.y + 88), 1
            )

        theme.text(s, "LEVEL REACHED", 13, theme.TEXT_DIM, (box.centerx, box.y + 112), anchor="center")
        theme.text(s, self.level, 32, theme.TEXT, (box.centerx, box.y + 142), anchor="center")

        theme.button(s, again, "RETRY", mouse, icon_name="replay", primary=True, size=19)
        theme.button(s, menu, "MAIN MENU", mouse, icon_name="home", size=19)