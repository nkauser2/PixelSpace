"""Shapes, letters and numbers that students can place on the canvas (R7).

There are three kinds of item:
    shape    8 simple shapes, each an outline of points (see below)
    letter   the capital letters A-Z
    number   the digits 0-9

Every shape outline fits inside a 1 x 1 box centered on (0, 0), so x and y
go from -0.5 to 0.5 (y grows downwards, like on the canvas). The browser
scales the outline up to the chosen size and fills it with the chosen color.
Letters and numbers are drawn by the browser as big bold text.
"""

import math


def _regular_polygon(sides, radius=0.5):
    """Corners of a shape with equal sides, with one corner pointing up."""
    points = []
    for i in range(sides):
        angle = math.radians(-90 + i * 360 / sides)
        points.append([round(radius * math.cos(angle), 4), round(radius * math.sin(angle), 4)])
    return points


def _star():
    points = []
    for i in range(10):  # alternate between outer and inner corners
        radius = 0.5 if i % 2 == 0 else 0.2
        angle = math.radians(-90 + i * 36)
        points.append([round(radius * math.cos(angle), 4), round(radius * math.sin(angle), 4)])
    return points


def _heart():
    # A well-known heart curve. Its raw size is about 32 wide by 29 tall,
    # so we shrink it to fit the 1 x 1 box and move it to the middle.
    raw = []
    for i in range(48):
        t = 2 * math.pi * i / 48
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        raw.append((x, y))
    top = min(y for _x, y in raw)
    bottom = max(y for _x, y in raw)
    scale = 1 / 32
    middle = (top + bottom) / 2
    return [[round(x * scale, 4), round((y - middle) * scale, 4)] for x, y in raw]


# Each shape's outline. A circle is just a polygon with lots of corners.
SHAPE_OUTLINES = {
    "circle": _regular_polygon(48),
    "square": [[-0.5, -0.5], [0.5, -0.5], [0.5, 0.5], [-0.5, 0.5]],
    "triangle": [[0, -0.5], [0.5, 0.5], [-0.5, 0.5]],
    "star": _star(),
    "heart": _heart(),
    "diamond": [[0, -0.5], [0.4, 0], [0, 0.5], [-0.4, 0]],
    "hexagon": _regular_polygon(6),
    "arrow": [[-0.5, -0.15], [0.1, -0.15], [0.1, -0.4], [0.5, 0], [0.1, 0.4], [0.1, 0.15], [-0.5, 0.15]],
}

LETTERS = [chr(code) for code in range(ord("A"), ord("Z") + 1)]
NUMBERS = [str(n) for n in range(10)]


def list_items():
    """Every item, in the order shown on the page.

    Each one looks like {"id": "star", "name": "Star", "kind": "shape"}.
    A letter's or number's id is the character itself, e.g. "A" or "7".
    """
    items = [{"id": sid, "name": sid.capitalize(), "kind": "shape"} for sid in SHAPE_OUTLINES]
    items += [{"id": letter, "name": letter, "kind": "letter"} for letter in LETTERS]
    items += [{"id": number, "name": number, "kind": "number"} for number in NUMBERS]
    return items


def is_item(item_id):
    """True if `item_id` is one of the items students can place."""
    return isinstance(item_id, str) and (item_id in SHAPE_OUTLINES or item_id in LETTERS or item_id in NUMBERS)
