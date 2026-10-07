from collections import namedtuple

import pygame

FONT_PATH = 'assets/fonts/PublicPixel.ttf'
fonts = {}

ORANGE = (235, 84, 40)
BROWN = (146, 52, 22)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# shadow is the color of a copy drawn one pixel down-left of the text, or None
Style = namedtuple('Style', 'size color shadow', defaults=(None,))

TITLE = Style(16, ORANGE, shadow=BROWN)
MENU = Style(16, BROWN)
SELECTED = Style(16, ORANGE, shadow=BROWN)
MARKER = Style(16, ORANGE)
HINT = Style(8, ORANGE)
WHITE_BIG = Style(16, WHITE)
WHITE_SMALL = Style(8, WHITE)

surfaces = {}


def get_font(size):
    # Fonts are shared per size so the glyph cache survives between frames. Building a
    # new Font every frame makes freetype re-rasterize every character from scratch.
    if size not in fonts:
        fonts[size] = pygame.font.Font(FONT_PATH, size)
    return fonts[size]


def wrap(text, font, width):
    # breaks at spaces so no line is wider than width pixels. '\n' still forces a break
    lines = []
    for paragraph in text.split('\n'):
        line = ''
        for word in paragraph.split(' '):
            longer = line + ' ' + word if line else word
            if line and font.size(longer)[0] > width:
                lines.append(line)
                line = word
            else:
                line = longer
        lines.append(line)
    return lines


def render_text(text, size, color, width=None):
    font = get_font(size)
    lines = text.split('\n') if width is None else wrap(text, font, width)
    images = [font.render(line, True, color) for line in lines]
    if len(images) == 1:
        return images[0]
    # multi-line text is stitched into one surface so drawing it is a single blit
    tops = [int(size * i * 1.2) for i in range(len(images))]
    surf = pygame.Surface(
        (max(img.get_width() for img in images), tops[-1] + images[-1].get_height()),
        pygame.SRCALPHA,
    )
    for i, img in enumerate(images):
        surf.blit(img, (0, tops[i]))
    return surf


def text_surface(text, size, color, width=None, cache=True):
    # Rendered text is kept, so drawing the same string again is a dict lookup and a blit.
    # Pass cache=False for text that changes nearly every frame (the level timer),
    # otherwise every value it ever shows stays in memory.
    if not cache:
        return render_text(text, size, color, width)
    key = (text, size, color, width)
    if key not in surfaces:
        surfaces[key] = render_text(text, size, color, width)
    return surfaces[key]


def draw_text(surf, text, pos, style, offset=(0, 0), width=None, cache=True):
    x, y = pos[0] - offset[0], pos[1] - offset[1]
    if style.shadow:
        surf.blit(text_surface(text, style.size, style.shadow, width, cache), (x - 1, y + 1))
    surf.blit(text_surface(text, style.size, style.color, width, cache), (x, y))
