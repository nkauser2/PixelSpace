"""Colors for PixelSpace (R2).

This file holds the built-in palette and checks that custom colors are valid.
Colors are written as hex codes, e.g. "#ff6b6b".
"""

import re

# PixelSpace's own palette. Each color has a friendly name for beginners.
PALETTE = [
    {"name": "Midnight", "hex": "#1f2333"},
    {"name": "Charcoal", "hex": "#4a4e5a"},
    {"name": "Cloud", "hex": "#c9ccd6"},
    {"name": "Snow", "hex": "#ffffff"},
    {"name": "Cherry", "hex": "#e63946"},
    {"name": "Coral", "hex": "#ff7f6b"},
    {"name": "Tangerine", "hex": "#ff9f1c"},
    {"name": "Sunflower", "hex": "#ffd23f"},
    {"name": "Lime", "hex": "#a7d948"},
    {"name": "Fern", "hex": "#2a9d5c"},
    {"name": "Mint", "hex": "#7fe0c3"},
    {"name": "Teal", "hex": "#16879b"},
    {"name": "Sky", "hex": "#5ab8f0"},
    {"name": "Ocean", "hex": "#2f5bd3"},
    {"name": "Grape", "hex": "#7b4fd6"},
    {"name": "Lavender", "hex": "#c3a6f2"},
    {"name": "Bubblegum", "hex": "#ff8fc7"},
    {"name": "Berry", "hex": "#b5246b"},
    {"name": "Cocoa", "hex": "#7a4b32"},
    {"name": "Sand", "hex": "#e9c99a"},
]

DEFAULT_COLOR = "#1f2333"

# Matches "#abc" or "#aabbcc" (letters can be upper or lower case).
_HEX_PATTERN = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def is_valid_hex(color):
    """Return True if `color` is a hex color like "#abc" or "#aabbcc"."""
    return isinstance(color, str) and bool(_HEX_PATTERN.match(color))


def normalize_hex(color):
    """Turn a valid hex color into the standard 7-character lowercase form.

    "#ABC" -> "#aabbcc".  Raises ValueError if the color is not valid.
    """
    if not is_valid_hex(color):
        raise ValueError(f"'{color}' is not a valid hex color (try something like #ff6b6b).")
    color = color.lower()
    if len(color) == 4:  # short form: double each digit
        color = "#" + "".join(ch * 2 for ch in color[1:])
    return color


# ---- Recent colors (R9) -------------------------------------------------

MAX_RECENT_COLORS = 5


class RecentColors:
    """Remembers the last few colors the user picked, newest first.

    Each color is kept only once: picking a color that is already in the
    list moves it to the front instead of adding it a second time.
    """

    def __init__(self, limit=MAX_RECENT_COLORS):
        self.limit = limit
        self._colors = []

    @property
    def colors(self):
        """A copy of the list, so nobody can change it by accident."""
        return list(self._colors)

    def pick(self, color):
        """Record that `color` was just picked. Returns the clean color.

        Raises ValueError (and changes nothing) if the color isn't valid.
        """
        color = normalize_hex(color)  # check it first; "#ABC" -> "#aabbcc"
        if color in self._colors:
            self._colors.remove(color)  # it will go back in at the front
        self._colors.insert(0, color)
        del self._colors[self.limit:]  # forget anything older than the limit
        return color
