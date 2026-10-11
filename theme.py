import math
import random

import pygame

BG = (8, 5, 24)
PANEL = (24, 16, 66)
PANEL_HOVER = (50, 34, 118)
FIELD = (14, 9, 44)
BORDER = (128, 92, 255)
BORDER_HI = (190, 160, 255)
LAVENDER = (181, 153, 255)
TEXT = (244, 238, 255)
TEXT_DIM = (150, 132, 210)
ACCENT = (255, 100, 216)
GOLD = (255, 214, 102)
SILVER = (205, 210, 235)
BRONZE = (232, 150, 92)
GOOD = (130, 255, 200)
BAD = (255, 100, 140)
BTN = (110, 70, 240)
BTN_HI = (150, 108, 255)
ICE = (120, 220, 255)
CYAN = (96, 224, 255)

INVADER_COLORS = [
    (120, 220, 255),
    (255, 120, 220),
    (150, 255, 200),
    (255, 214, 102),
    (181, 153, 255),
]

_fonts = {}


def font(size, bold=True):
    key = (size, bold)

    if key not in _fonts:
        _fonts[key] = pygame.font.SysFont("Arial", size, bold=bold)

    return _fonts[key]


def text(surface, message, size, color, pos, anchor="topleft", bold=True):
    rendered = font(size, bold).render(str(message), True, color)
    rect = rendered.get_rect()
    setattr(rect, anchor, pos)
    surface.blit(rendered, rect)
    return rect


def glow_text(surface, message, size, color, glow, pos, anchor="center"):
    f = font(size, True)
    base = f.render(str(message), True, color)
    shade = f.render(str(message), True, glow)
    shade.set_alpha(150)
    rect = base.get_rect()
    setattr(rect, anchor, pos)

    for dx, dy in (
        (-3, 0), (3, 0), (0, -3), (0, 3),
        (-2, -2), (2, -2), (-2, 2), (2, 2),
    ):
        surface.blit(shade, rect.move(dx, dy))

    surface.blit(base, rect)
    return rect


_title_fonts = {}
_title_cache = {}

TITLE_FONT_FILES = (
    "assets/fonts/title.ttf",
    "assets/fonts/title.otf",
)
TITLE_HEAVY_FONTS = (
    "arialblack",
    "segoeuiblack",
    "franklingothicheavy",
    "helveticaneue",
)


def title_font(size):
    if size not in _title_fonts:
        loaded = None

        for path in TITLE_FONT_FILES:
            try:
                loaded = pygame.font.Font(path, size)
                break
            except (pygame.error, FileNotFoundError, OSError):
                continue

        if loaded is None:
            for name in TITLE_HEAVY_FONTS:
                path = pygame.font.match_font(name)

                if path:
                    try:
                        loaded = pygame.font.Font(path, size)
                        break
                    except (pygame.error, OSError):
                        continue

        if loaded is None:
            loaded = pygame.font.SysFont("verdana,arial", size, bold=True)

        _title_fonts[size] = loaded

    return _title_fonts[size]


def _build_title(message, size, fill, extrude, outline):
    f = title_font(size)
    label = str(message)

    face = f.render(label, True, fill)
    side = f.render(label, True, extrude)
    edge = f.render(label, True, outline)

    w, h = face.get_size()
    depth = 4
    ring = 3
    pad = ring + 4

    canvas = pygame.Surface(
        (w + depth + pad * 2, h + depth + pad * 2), pygame.SRCALPHA
    )

    for d in range(depth + 1):
        for dx in range(-ring, ring + 1):
            for dy in range(-ring, ring + 1):
                if dx * dx + dy * dy <= ring * ring:
                    canvas.blit(edge, (pad + d + dx, pad + d + dy))

    for d in range(depth, 0, -1):
        canvas.blit(side, (pad + d, pad + d))

    canvas.blit(face, (pad, pad))

    return canvas


def fancy_text(
    surface,
    message,
    size,
    pos,
    fill=(255, 255, 255),
    extrude=(150, 100, 255),
    outline=(16, 8, 44),
    anchor="center",
    max_width=None,
):
    key = (str(message), size, fill, extrude, outline, max_width)

    if key not in _title_cache:
        built = _build_title(message, size, fill, extrude, outline)

        if max_width and built.get_width() > max_width:
            k = max_width / built.get_width()
            built = pygame.transform.smoothscale(
                built,
                (max_width, max(1, int(built.get_height() * k))),
            )

        _title_cache[key] = built

    image = _title_cache[key]
    rect = image.get_rect()
    setattr(rect, anchor, pos)
    surface.blit(image, rect)
    return rect


_INVADER = [
    "00100000100",
    "00010001000",
    "00111111100",
    "01101110110",
    "11111111111",
    "10111111101",
    "10100000101",
    "00011011000",
]


def make_invader(size, color):
    w, h = size
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cols, rows = 11, 8
    px = max(2, min(w // cols, h // rows))
    ox = (w - px * cols) // 2
    oy = (h - px * rows) // 2

    for r, row in enumerate(_INVADER):
        for c, ch in enumerate(row):
            if ch == "1":
                pygame.draw.rect(
                    surf, color, (ox + c * px, oy + r * px, px, px)
                )

    return surf


SHIP_STYLES = [
    {"body": (222, 230, 255), "wing": (84, 96, 230), "rim": (170, 190, 255), "glow": (90, 210, 255)},
    {"body": (255, 214, 214), "wing": (214, 56, 72), "rim": (255, 150, 150), "glow": (255, 176, 90)},
    {"body": (214, 255, 232), "wing": (36, 164, 108), "rim": (140, 240, 190), "glow": (120, 255, 190)},
    {"body": (238, 210, 255), "wing": (146, 58, 226), "rim": (206, 150, 255), "glow": (255, 110, 230)},
]


def make_ship(size, style=0):
    w, h = size
    st = SHIP_STYLES[style % len(SHIP_STYLES)]
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    def pts(*coords):
        return [(int(x * w), int(y * h)) for x, y in coords]

    pygame.draw.polygon(
        surf, st["glow"], pts((0.43, 0.80), (0.57, 0.80), (0.50, 1.0))
    )

    wings = pts(
        (0.50, 0.36), (0.98, 0.86), (0.80, 0.88),
        (0.50, 0.70), (0.20, 0.88), (0.02, 0.86),
    )
    pygame.draw.polygon(surf, st["wing"], wings)
    pygame.draw.polygon(surf, st["rim"], wings, 2)

    body = pts(
        (0.50, 0.02), (0.61, 0.30), (0.59, 0.80),
        (0.50, 0.90), (0.41, 0.80), (0.39, 0.30),
    )
    pygame.draw.polygon(surf, st["body"], body)
    pygame.draw.polygon(surf, st["rim"], body, 2)

    pygame.draw.ellipse(
        surf,
        st["glow"],
        (int(w * 0.44), int(h * 0.26), max(2, int(w * 0.12)), max(2, int(h * 0.24))),
    )

    return surf


def make_orb(size, color):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2

    for i in range(center, 0, -1):
        k = i / center
        alpha = int(255 * (1 - k) + 40)
        col = (
            min(255, int(color[0] * (1 - k * 0.4) + 60 * (1 - k))),
            min(255, int(color[1] * (1 - k * 0.4) + 60 * (1 - k))),
            min(255, int(color[2] * (1 - k * 0.4) + 60 * (1 - k))),
            min(255, alpha),
        )
        pygame.draw.circle(surf, col, (center, center), i)

    return surf


def load_image(path, size, fallback):
    try:
        image = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(image, size)
    except (pygame.error, FileNotFoundError, OSError):
        return fallback()


AVATAR_STYLES = [
    {"hair": (150, 80, 235), "bg": (60, 36, 130), "eye": (255, 120, 220)},
    {"hair": (40, 140, 255), "bg": (24, 48, 120), "eye": (120, 230, 255)},
    {"hair": (255, 150, 60), "bg": (110, 52, 40), "eye": (255, 214, 102)},
    {"hair": (44, 38, 78), "bg": (36, 30, 80), "eye": (190, 160, 255)},
]

_avatar_cache = {}


def _circle_clip(surf):
    size = surf.get_width()
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(
        mask, (255, 255, 255, 255), (size // 2, size // 2), size // 2
    )
    surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)


def make_avatar(size, index=0):
    st = AVATAR_STYLES[index % len(AVATAR_STYLES)]
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size / 2

    pygame.draw.circle(surf, st["bg"], (c, c), c)
    pygame.draw.circle(surf, st["hair"], (c, c * 0.95), size * 0.36)
    pygame.draw.ellipse(
        surf, (255, 226, 206),
        (c - size * 0.24, c - size * 0.20, size * 0.48, size * 0.56),
    )
    pygame.draw.ellipse(
        surf, st["hair"],
        (c - size * 0.28, c - size * 0.34, size * 0.56, size * 0.34),
    )

    for sign in (-1, 1):
        ex = c + sign * size * 0.11
        pygame.draw.ellipse(
            surf, st["eye"],
            (ex - size * 0.045, c + size * 0.02, size * 0.09, size * 0.14),
        )
        pygame.draw.circle(
            surf, (20, 10, 40),
            (int(ex), int(c + size * 0.10)), max(1, int(size * 0.025)),
        )

    _circle_clip(surf)
    pygame.draw.circle(surf, BORDER_HI, (int(c), int(c)), int(c), 2)

    return surf


def avatar_image(index, size):
    key = (index, size)

    if key not in _avatar_cache:
        try:
            img = pygame.image.load(
                f"assets/images/avatar{index + 1}.png"
            ).convert_alpha()
            img = pygame.transform.smoothscale(img, (size, size))
            _circle_clip(img)
            pygame.draw.circle(
                img, BORDER_HI, (size // 2, size // 2), size // 2, 2
            )
        except (pygame.error, FileNotFoundError, OSError):
            img = make_avatar(size, index)

        _avatar_cache[key] = img

    return _avatar_cache[key]


def draw_avatar(surface, center, radius, index):
    img = avatar_image(index, radius * 2)
    surface.blit(img, img.get_rect(center=center))


def _lerp(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(len(a)))


class Backdrop:
    def __init__(
        self, w, h, scroll=False, planets=True, grid=True, seed=11,
        image=None,
    ):
        self.w = w
        self.h = h
        self.scroll = scroll
        self.has_image = False

        if image:
            try:
                picture = pygame.image.load(image).convert()
                self.base = pygame.transform.smoothscale(picture, (w, h))
                self.stars = []
                self.has_image = True
                return
            except (pygame.error, FileNotFoundError, OSError):
                print(f"Background image missing: {image}")

        rnd = random.Random(seed)

        self.stars = [
            (
                rnd.randrange(w),
                rnd.randrange(h),
                rnd.choice((1, 1, 1, 2, 2, 3)),
                rnd.random() * 6.283,
            )
            for _ in range(130)
        ]

        self.base = pygame.Surface((w, h))
        self._gradient()
        self._nebula()

        if planets:
            self._planets()

        if grid:
            self._mountains(rnd)

    def _gradient(self):
        stops = [(0.0, (8, 5, 28)), (0.55, (26, 12, 78)), (1.0, (46, 20, 112))]

        for y in range(self.h):
            k = y / self.h

            for i in range(len(stops) - 1):
                if stops[i][0] <= k <= stops[i + 1][0]:
                    span = stops[i + 1][0] - stops[i][0]
                    color = _lerp(
                        stops[i][1], stops[i + 1][1], (k - stops[i][0]) / span
                    )
                    break

            pygame.draw.line(self.base, color, (0, y), (self.w, y))

    def _nebula(self):
        blobs = (
            ((100, 44, 220), 0.18, 0.28, 0.38, 120),
            ((210, 56, 200), 0.82, 0.42, 0.30, 80),
            ((56, 90, 230), 0.55, 0.78, 0.40, 90),
            ((140, 60, 240), 0.35, 0.62, 0.28, 70),
        )
        sw, sh = self.w // 8, self.h // 8

        for color, fx, fy, fr, alpha in blobs:
            tiny = pygame.Surface((sw, sh), pygame.SRCALPHA)
            cx, cy = int(sw * fx), int(sh * fy)
            radius = max(2, int(sw * fr))

            for r in range(radius, 0, -1):
                a = int(alpha * (1 - r / radius) ** 1.4)
                pygame.draw.circle(tiny, (*color, a), (cx, cy), r)

            self.base.blit(
                pygame.transform.smoothscale(tiny, (self.w, self.h)), (0, 0)
            )

    def _sphere(self, cx, cy, radius, light, dark):
        for r in range(radius, 0, -2):
            k = 1 - r / radius
            shift = (radius - r) * 0.38
            pygame.draw.circle(
                self.base,
                _lerp(dark, light, k),
                (int(cx - shift), int(cy - shift)),
                r,
            )

        pygame.draw.circle(self.base, _lerp(dark, light, 0.5), (cx, cy), radius, 2)

    def _planet(self, cx, cy, radius, light, dark, ring=None):
        if ring:
            rect = pygame.Rect(
                cx - radius * 1.6, cy - radius * 0.28,
                radius * 3.2, radius * 0.56,
            )
            pygame.draw.arc(self.base, ring, rect, 0, math.pi, 3)

        self._sphere(cx, cy, radius, light, dark)

        if ring:
            pygame.draw.arc(self.base, ring, rect, math.pi, 2 * math.pi, 3)

    def _planets(self):
        self._planet(
            72, 96, 72, (168, 120, 255), (34, 18, 96), ring=(196, 160, 255)
        )
        self._planet(
            self.w - 54, 150, 48, (120, 150, 255), (26, 26, 96)
        )

    def _mountains(self, rnd):
        layers = (
            ((30, 14, 80), self.h - 70, 60, (112, 72, 224)),
            ((16, 8, 50), self.h - 30, 40, (150, 100, 255)),
        )

        for color, base, amp, edge in layers:
            pts = [(0, self.h)]
            x = 0

            while x <= self.w + 40:
                pts.append((x, base - rnd.randint(0, amp)))
                x += rnd.randint(30, 70)

            pts.append((self.w, self.h))

            pygame.draw.polygon(self.base, color, pts)
            pygame.draw.lines(self.base, edge, False, pts[1:-1], 2)

    def draw(self, surface):
        t = pygame.time.get_ticks() / 1000.0
        surface.blit(self.base, (0, 0))

        for x, y, size, phase in self.stars:
            if self.scroll:
                y = (y + t * 18 * size) % self.h

            b = 0.55 + 0.45 * math.sin(t * 2 + phase)
            color = (
                int(150 * b + 90),
                int(130 * b + 80),
                int(255 * b),
            )
            pygame.draw.circle(surface, color, (int(x), int(y)), size)


class StarField:
    LAYERS = (
        (90, 1, 10, 2.0),
        (50, 1, 26, 3.0),
        (24, 2, 52, 2.4),
    )
    TINTS = ((255, 255, 255), (190, 205, 255), (255, 200, 245), (200, 180, 255))

    def __init__(self, w, h, seed=5):
        self.w = w
        self.h = h
        rnd = random.Random(seed)
        self.stars = []

        for count, size, speed, twinkle in self.LAYERS:
            for _ in range(count):
                self.stars.append(
                    (
                        rnd.randrange(w),
                        rnd.uniform(0, h),
                        size,
                        speed * rnd.uniform(0.8, 1.2),
                        twinkle * rnd.uniform(0.7, 1.3),
                        rnd.random() * 6.283,
                        rnd.choice(self.TINTS),
                    )
                )

    def _shooting(self, surface, t):
        for k, period in enumerate((7.0, 11.0)):
            cycle, phase = divmod(t / period + k * 0.37, 1.0)

            if phase > 0.10:
                continue

            prog = phase / 0.10
            rnd = random.Random(int(cycle) * 13 + k)
            sx = rnd.uniform(self.w * 0.3, self.w)
            sy = rnd.uniform(0, self.h * 0.45)
            hx = sx - prog * 320
            hy = sy + prog * 160
            fade = 1.0 - prog

            for i in range(8):
                f = i / 8
                col = int(255 * fade * (1 - f))
                pygame.draw.line(
                    surface,
                    (col, col, min(255, col + 20)),
                    (int(hx + f * 60), int(hy - f * 30)),
                    (int(hx + (f + 0.125) * 60), int(hy - (f + 0.125) * 30)),
                    2 if i < 3 else 1,
                )

    def draw(self, surface):
        t = pygame.time.get_ticks() / 1000.0
        surface.fill((2, 2, 10))

        for x, y0, size, speed, twinkle, phase, tint in self.stars:
            y = (y0 + t * speed) % self.h
            b = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * twinkle + phase))
            color = tuple(int(c * b) for c in tint)

            if size >= 2:
                halo = tuple(int(c * b * 0.25) for c in tint)
                pygame.draw.circle(surface, halo, (int(x), int(y)), 4)

            pygame.draw.circle(surface, color, (int(x), int(y)), size)

        self._shooting(surface, t)


_cache = {}


def _poly(w, h, cut, ox=0, oy=0):
    return [
        (ox + cut, oy),
        (ox + w - cut, oy),
        (ox + w, oy + cut),
        (ox + w, oy + h - cut),
        (ox + w - cut, oy + h),
        (ox + cut, oy + h),
        (ox, oy + h - cut),
        (ox, oy + cut),
    ]


def _gradient_poly(w, h, top, bottom, cut, alpha=255):
    grad = pygame.Surface((w, h), pygame.SRCALPHA)

    for y in range(h):
        grad.fill(
            (*_lerp(top, bottom, y / max(1, h - 1)), alpha), (0, y, w, 1)
        )

    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(mask, (255, 255, 255, 255), _poly(w - 1, h - 1, cut))
    grad.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    return grad


def _glow(surf, w, h, cut, color, m, rings=5, strength=10):
    for i in range(rings, 0, -1):
        a = strength + (rings - i) * strength
        pts = _poly(w - 1 + 2 * i, h - 1 + 2 * i, cut + i, m - i, m - i)
        pygame.draw.lines(surf, (*color, a), True, pts, 2)


def _panel_surface(w, h, border, fill, cut, glow, thin=False):
    key = ("p", w, h, border, fill, cut, glow, thin)

    if key in _cache:
        return _cache[key]

    m = 12 if glow else 2
    surf = pygame.Surface((w + 2 * m, h + 2 * m), pygame.SRCALPHA)

    if glow:
        if thin:
            _glow(surf, w, h, cut, border, m, rings=3, strength=7)
        else:
            _glow(surf, w, h, cut, border, m)

    surf.blit(
        _gradient_poly(w, h, _lerp(fill, (255, 255, 255), 0.08), fill, cut, 228),
        (m, m),
    )

    pts = _poly(w - 1, h - 1, cut, m, m)
    pygame.draw.lines(surf, border, True, pts, 1 if thin else 2)

    if not thin:
        inner = _poly(w - 13, h - 13, max(2, cut - 4), m + 6, m + 6)
        pygame.draw.lines(surf, (*_lerp(border, fill, 0.55), 130), True, inner, 1)

    for a, b in ((1, 2), (3, 4), (5, 6), (7, 0)):
        pygame.draw.line(surf, BORDER_HI, pts[a], pts[b], 2 if thin else 3)

    _cache[key] = (surf, m)
    return _cache[key]


def panel(
    surface, rect, border=BORDER, fill=PANEL, radius=None, glow=True, cut=16,
    thin=False,
):
    rect = pygame.Rect(rect)

    if radius is not None:
        cut = radius

    surf, m = _panel_surface(
        rect.w, rect.h, tuple(border), tuple(fill), cut, glow, thin
    )
    surface.blit(surf, (rect.x - m, rect.y - m))


_BTN_STYLES = {
    "normal": ((62, 40, 150), (30, 20, 88), BORDER),
    "normal_hover": ((92, 62, 205), (48, 32, 126), BORDER_HI),
    "primary": ((128, 84, 255), (78, 44, 186), BORDER_HI),
    "primary_hover": ((158, 116, 255), (100, 62, 215), (225, 210, 255)),
    "danger": ((120, 34, 92), (64, 20, 58), BAD),
    "danger_hover": ((158, 46, 116), (88, 28, 76), (255, 150, 180)),
}


def _button_surface(w, h, style, cut):
    key = ("b", w, h, style, cut)

    if key in _cache:
        return _cache[key]

    m = 8
    top, bottom, border = _BTN_STYLES[style]
    surf = pygame.Surface((w + 2 * m, h + 2 * m), pygame.SRCALPHA)

    _glow(surf, w, h, cut, border, m, rings=4, strength=12)
    surf.blit(_gradient_poly(w, h, top, bottom, cut), (m, m))

    gloss = pygame.Surface((max(1, w - 2 * cut), max(1, h // 2 - 3)), pygame.SRCALPHA)
    gloss.fill((255, 255, 255, 22))
    surf.blit(gloss, (m + cut, m + 3))

    pts = _poly(w - 1, h - 1, cut, m, m)
    pygame.draw.lines(surf, border, True, pts, 2)

    _cache[key] = (surf, m)
    return _cache[key]


def button(
    surface,
    rect,
    label,
    mouse,
    icon_name=None,
    primary=False,
    danger=False,
    size=20,
    align="center",
):
    rect = pygame.Rect(rect)
    hover = rect.collidepoint(mouse)

    kind = "primary" if primary else "danger" if danger else "normal"
    style = kind + ("_hover" if hover else "")
    cut = max(4, min(12, rect.h // 4))

    surf, m = _button_surface(rect.w, rect.h, style, cut)
    surface.blit(surf, (rect.x - m, rect.y - m))

    rendered = font(size).render(label, True, TEXT) if label else None

    if align == "left" and icon_name:
        icon(surface, icon_name, rect.x + 36, rect.centery, TEXT, 1.1)

        if rendered:
            surface.blit(
                rendered,
                rendered.get_rect(center=(rect.centerx + 16, rect.centery)),
            )
    else:
        icon_w = 30 if icon_name else 0
        total = icon_w + (rendered.get_width() if rendered else 0)
        start = rect.centerx - total // 2

        if icon_name:
            icon(surface, icon_name, start + 10, rect.centery, TEXT, 1.0)

        if rendered:
            surface.blit(
                rendered,
                (start + icon_w, rect.centery - rendered.get_height() // 2),
            )

    return hover


def switch(surface, rect, on):
    rect = pygame.Rect(rect)
    radius = rect.h // 2

    if on:
        halo = pygame.Surface((rect.w + 16, rect.h + 16), pygame.SRCALPHA)
        pygame.draw.rect(
            halo, (*BTN_HI, 46), halo.get_rect(), border_radius=radius + 8
        )
        surface.blit(halo, (rect.x - 8, rect.y - 8))

    pygame.draw.rect(
        surface, (122, 80, 255) if on else (40, 32, 84), rect, border_radius=radius
    )
    pygame.draw.rect(
        surface,
        BORDER_HI if on else BORDER,
        rect,
        2,
        border_radius=radius,
    )

    knob_x = rect.right - radius if on else rect.x + radius
    pygame.draw.circle(surface, TEXT, (knob_x, rect.centery), radius - 5)


def bar(surface, rect, frac, color, back=FIELD, border=BORDER):
    rect = pygame.Rect(rect)
    frac = max(0.0, min(1.0, frac))
    radius = rect.h // 2

    pygame.draw.rect(surface, back, rect, border_radius=radius)

    if frac > 0:
        fill = rect.copy()
        fill.w = max(rect.h, int(rect.w * frac))
        pygame.draw.rect(surface, color, fill, border_radius=radius)

    pygame.draw.rect(surface, border, rect, 2, border_radius=radius)


def icon(surface, name, cx, cy, color, s=1.0, width=2):
    u = 10 * s
    d = pygame.draw

    def P(x, y):
        return (int(cx + x * u), int(cy + y * u))

    def R(x, y, w, h):
        return (int(cx + x * u), int(cy + y * u), int(w * u), int(h * u))

    def Q(x, y, a=math.radians(45)):
        return P(
            x * math.cos(a) - y * math.sin(a),
            x * math.sin(a) + y * math.cos(a),
        )

    if name == "user":
        d.circle(surface, color, P(0, -0.4), max(2, int(0.5 * u)), width)
        d.arc(surface, color, R(-0.9, 0.15, 1.8, 1.5), 0, math.pi, width)

    elif name == "lock":
        d.rect(
            surface, color, R(-0.7, -0.05, 1.4, 1.0), width, border_radius=2
        )
        d.arc(surface, color, R(-0.45, -0.85, 0.9, 1.0), 0, math.pi, width)

    elif name in ("eye", "eye_off"):
        d.ellipse(surface, color, R(-1.0, -0.55, 2.0, 1.1), width)
        d.circle(surface, color, P(0, 0), max(2, int(0.3 * u)))

        if name == "eye_off":
            d.line(surface, color, P(-0.9, 0.8), P(0.9, -0.8), width + 1)

    elif name == "trophy":
        d.polygon(
            surface,
            color,
            [P(-0.7, -0.8), P(0.7, -0.8), P(0.5, 0.1), P(-0.5, 0.1)],
            width,
        )
        d.line(surface, color, P(0, 0.1), P(0, 0.6), width)
        d.line(surface, color, P(-0.5, 0.75), P(0.5, 0.75), width)
        d.circle(surface, color, P(-0.9, -0.4), max(2, int(0.28 * u)), width)
        d.circle(surface, color, P(0.9, -0.4), max(2, int(0.28 * u)), width)

    elif name == "play":
        d.polygon(surface, color, [P(-0.5, -0.7), P(-0.5, 0.7), P(0.7, 0)])

    elif name == "gear":
        d.circle(surface, color, P(0, 0), max(2, int(0.55 * u)), width)
        d.circle(surface, color, P(0, 0), max(1, int(0.18 * u)))

        for i in range(8):
            a = i * math.pi / 4
            d.line(
                surface,
                color,
                P(math.cos(a) * 0.72, math.sin(a) * 0.72),
                P(math.cos(a) * 1.0, math.sin(a) * 1.0),
                width + 1,
            )

    elif name == "exit":
        d.lines(
            surface,
            color,
            False,
            [P(-0.2, -0.85), P(-0.95, -0.85), P(-0.95, 0.85), P(-0.2, 0.85)],
            width,
        )
        d.line(surface, color, P(-0.3, 0), P(0.9, 0), width)
        d.line(surface, color, P(0.9, 0), P(0.4, -0.5), width)
        d.line(surface, color, P(0.9, 0), P(0.4, 0.5), width)

    elif name == "back":
        d.line(surface, color, P(0.8, 0), P(-0.8, 0), width)
        d.line(surface, color, P(-0.8, 0), P(-0.2, -0.6), width)
        d.line(surface, color, P(-0.8, 0), P(-0.2, 0.6), width)

    elif name == "arrow_right":
        d.line(surface, color, P(-0.8, 0), P(0.8, 0), width)
        d.line(surface, color, P(0.8, 0), P(0.2, -0.6), width)
        d.line(surface, color, P(0.8, 0), P(0.2, 0.6), width)

    elif name == "heart":
        d.circle(surface, color, P(-0.42, -0.25), max(2, int(0.5 * u)))
        d.circle(surface, color, P(0.42, -0.25), max(2, int(0.5 * u)))
        d.polygon(surface, color, [P(-0.88, 0.0), P(0.88, 0.0), P(0, 0.95)])

    elif name == "pause":
        d.rect(surface, color, R(-0.55, -0.7, 0.4, 1.4))
        d.rect(surface, color, R(0.15, -0.7, 0.4, 1.4))

    elif name == "check":
        d.lines(
            surface,
            color,
            False,
            [P(-0.8, 0.05), P(-0.25, 0.6), P(0.8, -0.6)],
            width + 1,
        )

    elif name == "cross":
        d.line(surface, color, P(-0.6, -0.6), P(0.6, 0.6), width + 1)
        d.line(surface, color, P(-0.6, 0.6), P(0.6, -0.6), width + 1)

    elif name == "plus":
        d.line(surface, color, P(-0.7, 0), P(0.7, 0), width + 1)
        d.line(surface, color, P(0, -0.7), P(0, 0.7), width + 1)

    elif name == "star":
        pts = []

        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            r = 1.0 if i % 2 == 0 else 0.42
            pts.append(P(math.cos(a) * r, math.sin(a) * r))

        d.polygon(surface, color, pts, width)

    elif name == "pencil":
        d.line(surface, color, P(-0.6, 0.6), P(0.7, -0.7), width + 2)
        d.polygon(
            surface, color, [P(-0.95, 0.95), P(-0.95, 0.4), P(-0.4, 0.95)]
        )

    elif name == "trash":
        d.line(surface, color, P(-0.85, -0.5), P(0.85, -0.5), width)
        d.line(surface, color, P(-0.25, -0.8), P(0.25, -0.8), width)
        d.polygon(
            surface,
            color,
            [P(-0.6, -0.4), P(0.6, -0.4), P(0.5, 0.9), P(-0.5, 0.9)],
            width,
        )
        d.line(surface, color, P(-0.2, -0.1), P(-0.2, 0.6), 1)
        d.line(surface, color, P(0.2, -0.1), P(0.2, 0.6), 1)

    elif name in ("speaker", "speaker_off"):
        d.polygon(
            surface,
            color,
            [
                P(-0.9, -0.3),
                P(-0.4, -0.3),
                P(0.1, -0.8),
                P(0.1, 0.8),
                P(-0.4, 0.3),
                P(-0.9, 0.3),
            ],
            width,
        )

        if name == "speaker":
            d.arc(surface, color, R(-0.2, -0.55, 1.1, 1.1), -1.0, 1.0, width)
        else:
            d.line(surface, color, P(0.4, -0.4), P(1.0, 0.4), width)
            d.line(surface, color, P(0.4, 0.4), P(1.0, -0.4), width)

    elif name == "music":
        d.circle(surface, color, P(-0.3, 0.6), max(2, int(0.35 * u)))
        d.line(surface, color, P(0.05, 0.6), P(0.05, -0.8), width)
        d.line(surface, color, P(0.05, -0.8), P(0.8, -0.5), width)

    elif name == "replay":
        d.arc(surface, color, R(-0.7, -0.7, 1.4, 1.4), 0.7, 6.0, width)
        d.polygon(
            surface, color, [P(0.2, -0.85), P(0.95, -0.75), P(0.7, -0.05)]
        )

    elif name == "home":
        d.polygon(surface, color, [P(-0.95, 0), P(0, -0.9), P(0.95, 0)])
        d.rect(surface, color, R(-0.65, 0.0, 1.3, 0.9))

    elif name == "shield":
        d.polygon(
            surface,
            color,
            [
                P(0, -0.95),
                P(0.75, -0.55),
                P(0.65, 0.3),
                P(0, 0.95),
                P(-0.65, 0.3),
                P(-0.75, -0.55),
            ],
            width,
        )

    elif name == "bolt":
        d.polygon(
            surface,
            color,
            [
                P(0.2, -0.95),
                P(-0.6, 0.15),
                P(-0.05, 0.15),
                P(-0.25, 0.95),
                P(0.6, -0.2),
                P(0.05, -0.2),
            ],
        )

    elif name == "triple":
        d.line(surface, color, P(0, 0.8), P(-0.75, -0.8), width + 1)
        d.line(surface, color, P(0, 0.8), P(0, -0.9), width + 1)
        d.line(surface, color, P(0, 0.8), P(0.75, -0.8), width + 1)

    elif name == "crown":
        d.polygon(
            surface,
            color,
            [
                P(-0.9, 0.6),
                P(-0.9, -0.5),
                P(-0.4, 0.0),
                P(0, -0.7),
                P(0.4, 0.0),
                P(0.9, -0.5),
                P(0.9, 0.6),
            ],
        )

    elif name == "pad":
        d.line(surface, color, P(-0.85, 0), P(0.85, 0), width + 2)
        d.line(surface, color, P(0, -0.85), P(0, 0.85), width + 2)
        d.circle(surface, color, P(0, 0), max(2, int(0.3 * u)), width)

    elif name == "rocket":
        d.polygon(
            surface,
            color,
            [Q(0, -1.0), Q(0.42, -0.4), Q(0.42, 0.5), Q(-0.42, 0.5), Q(-0.42, -0.4)],
        )
        d.polygon(
            surface, color, [Q(0.42, 0.0), Q(0.8, 0.7), Q(0.42, 0.5)]
        )
        d.polygon(
            surface, color, [Q(-0.42, 0.0), Q(-0.8, 0.7), Q(-0.42, 0.5)]
        )
        d.polygon(
            surface, color, [Q(-0.25, 0.6), Q(0.25, 0.6), Q(0, 1.1)]
        )
        d.circle(surface, (40, 24, 110), Q(0, -0.25), max(2, int(0.18 * u)))

    elif name == "skull":
        dark = (14, 8, 40)
        d.circle(surface, color, P(0, -0.2), max(3, int(0.8 * u)))
        d.rect(surface, color, R(-0.45, 0.35, 0.9, 0.6), border_radius=2)
        d.circle(surface, dark, P(-0.3, -0.2), max(2, int(0.22 * u)))
        d.circle(surface, dark, P(0.3, -0.2), max(2, int(0.22 * u)))
        d.polygon(surface, dark, [P(0, 0.05), P(-0.1, 0.3), P(0.1, 0.3)])
        d.line(surface, dark, P(-0.15, 0.55), P(-0.15, 0.95), 1)
        d.line(surface, dark, P(0.15, 0.55), P(0.15, 0.95), 1)

    elif name == "save":
        d.rect(
            surface, color, R(-0.85, -0.85, 1.7, 1.7), width, border_radius=2
        )
        d.rect(surface, color, R(-0.5, -0.85, 1.0, 0.6), width)
        d.rect(surface, color, R(-0.5, 0.1, 1.0, 0.75), width)