import pygame

import theme


class MobileButtons:
    def __init__(self):
        self.left = pygame.Rect(16, 546, 52, 40)
        self.right = pygame.Rect(76, 546, 52, 40)
        self.fire = pygame.Rect(732, 546, 52, 40)

    def _draw_button(self, screen, rect, icon_name, fill, border):
        mouse = pygame.mouse.get_pos()
        pressed = (
            pygame.mouse.get_pressed()[0] and rect.collidepoint(mouse)
        )

        color = theme.PANEL_HOVER if pressed else fill

        pygame.draw.rect(screen, color, rect, border_radius=10)
        pygame.draw.rect(screen, border, rect, 2, border_radius=10)
        theme.icon(
            screen,
            icon_name,
            rect.centerx,
            rect.centery,
            theme.TEXT,
            0.9,
        )

    def draw(self, screen):
        self._draw_button(
            screen, self.left, "back", theme.PANEL, theme.BORDER
        )
        self._draw_button(
            screen, self.right, "arrow_right", theme.PANEL, theme.BORDER
        )
        self._draw_button(
            screen, self.fire, "bolt", (96, 32, 74), theme.ACCENT
        )

    def handle_mouse(self, player, events):
        """Mo-move sa player ug mo-return True kung gigunitan ang fire."""
        fire_held = False

        if pygame.mouse.get_pressed()[0]:
            mouse_pos = pygame.mouse.get_pos()

            if self.left.collidepoint(mouse_pos):
                player.move_left()

            if self.right.collidepoint(mouse_pos):
                player.move_right()

            if self.fire.collidepoint(mouse_pos):
                fire_held = True

        return fire_held