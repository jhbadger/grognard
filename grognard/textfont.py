"""Smooth text: what the windows need to draw the game's text in a real
font over the picture, instead of the bitmap font in it.

The game lays text out in its own pixels (640 x 480), so a font is
chosen to match the bitmap font's size once the picture is scaled up to
the window: capitals about 7 of the game's pixels tall.  A game can name
its own with FONT = dict(family='Georgia', size=1.0, bold=False); size
is a factor on the usual size.
"""

SIZE = 9.6          # pixel size of the font at scale 1 and zoom 1
CAPS = 0.71         # how much of the pixel size a capital letter is


def spec(gdef):
    d = dict(family=None, size=1.0, bold=False)
    d.update(getattr(gdef, 'FONT', {}) or {})
    return d


def pixels(scale, zoom, factor=1.0):
    """The font's pixel size for text at scale, with the picture zoomed
    by zoom."""
    return max(5, int(round(SIZE * factor * scale * zoom)))
