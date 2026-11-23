"""The drawing document for PixelSpace.

The browser draws on the screen, but the artwork itself is stored here.
Keeping it in Python lets us test drawing (R3), erasing (R4), undo/redo (R5),
placed shapes/letters/numbers (R7), clearing (R8) and flip/rotate (R11)
without a browser.

The artwork is one list, drawn in order from first to last, so newer marks
cover older ones. (It is called `strokes` because that is the name used in
save files since Round 1.) It holds two kinds of entry:

A brush or eraser stroke:
    {"tool": "brush", "color": "#e63946", "size": 8, "points": [[10, 20], [12, 24]]}

A placed shape, letter or number (R7), filled with one color:
    {"tool": "item", "item": "star", "color": "#e63946", "size": 120,
     "x": 400, "y": 300, "rotation": 90, "flip_x": False, "flip_y": False}
  x and y are the item's center, size is the width of its square box,
  rotation is 0, 90, 180 or 270 degrees clockwise, and flip_x / flip_y
  say whether it is mirrored (see item_point_on_canvas for the exact rule).
"""

import copy
import math

from colors import normalize_hex
from shapes import is_item

CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600

TOOLS = ("brush", "eraser")
MIN_SIZE = 1
MAX_SIZE = 100
MAX_POINTS = 10_000  # stops one stroke from being absurdly large

# Placed items (R7) and flip/rotate (R11)
MIN_ITEM_SIZE = 20
MAX_ITEM_SIZE = 400
DEFAULT_ITEM_SIZE = 120
ROTATIONS = (0, 90, 180, 270)
FLIP_DIRECTIONS = ("horizontal", "vertical")


def _is_number(value):
    """True for ordinary numbers like 3 or 2.5 (not True/False, not NaN or infinity)."""
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def make_stroke(tool, color, size, points):
    """Check a stroke's details and return a clean stroke dictionary.

    Raises ValueError with a friendly message if anything is wrong.
    """
    if tool not in TOOLS:
        raise ValueError(f"Unknown tool '{tool}'. Choose one of: {', '.join(TOOLS)}.")

    # The eraser doesn't need a color; the brush must have a valid one.
    clean_color = None if tool == "eraser" else normalize_hex(color)

    # bool is a kind of int in Python, so rule it out on purpose.
    if isinstance(size, bool) or not isinstance(size, (int, float)):
        raise ValueError("Brush size must be a number.")
    if not MIN_SIZE <= size <= MAX_SIZE:
        raise ValueError(f"Brush size must be between {MIN_SIZE} and {MAX_SIZE}.")

    if not isinstance(points, list) or len(points) == 0:
        raise ValueError("A stroke needs at least one point.")
    if len(points) > MAX_POINTS:
        raise ValueError(f"A stroke can have at most {MAX_POINTS} points.")

    clean_points = []
    for point in points:
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise ValueError("Each point must be a pair of numbers like [x, y].")
        x, y = point
        for value in (x, y):
            if not _is_number(value):
                raise ValueError("Point coordinates must be ordinary numbers.")
        clean_points.append([round(float(x), 1), round(float(y), 1)])

    return {"tool": tool, "color": clean_color, "size": size, "points": clean_points}


def make_item(item, color, size, x, y, rotation=0, flip_x=False, flip_y=False):
    """Check a placed item's details (R7, R11) and return a clean item dictionary.

    Raises ValueError with a friendly message if anything is wrong.
    """
    if not is_item(item):
        raise ValueError(f"'{item}' isn't one of the shapes, letters or numbers you can place.")
    clean_color = normalize_hex(color)
    if not _is_number(size) or not MIN_ITEM_SIZE <= size <= MAX_ITEM_SIZE:
        raise ValueError(f"Item size must be a number between {MIN_ITEM_SIZE} and {MAX_ITEM_SIZE}.")
    if not _is_number(x) or not _is_number(y) or not (0 <= x <= CANVAS_WIDTH and 0 <= y <= CANVAS_HEIGHT):
        raise ValueError("Items must be placed on the canvas.")
    if isinstance(rotation, bool) or rotation not in ROTATIONS:
        raise ValueError("Rotation must be 0, 90, 180 or 270 degrees.")
    if not isinstance(flip_x, bool) or not isinstance(flip_y, bool):
        raise ValueError("Flips must be true or false.")
    return {
        "tool": "item", "item": item, "color": clean_color, "size": size,
        "x": round(float(x), 1), "y": round(float(y), 1),
        "rotation": rotation, "flip_x": flip_x, "flip_y": flip_y,
    }


def item_point_on_canvas(item, local_x, local_y):
    """Where a point of an item's 1 x 1 box ends up on the canvas.

    (local_x, local_y) go from -0.5 to 0.5, with (0, 0) the item's center.
    The steps are: mirror (flip_x / flip_y), grow to the item's size, turn
    clockwise by `rotation`, then move to the item's center. static/app.js
    draws items with these same steps in the same order.
    """
    x = local_x * item["size"] * (-1 if item["flip_x"] else 1)
    y = local_y * item["size"] * (-1 if item["flip_y"] else 1)
    angle = math.radians(item["rotation"])
    # On screens y grows downwards, so this turns clockwise.
    turned_x = x * math.cos(angle) - y * math.sin(angle)
    turned_y = x * math.sin(angle) + y * math.cos(angle)
    return (item["x"] + turned_x, item["y"] + turned_y)


class Canvas:
    """One piece of artwork: its strokes and items, its template (only in
    artwork saved before Round 3), and its undo/redo history.

    How undo/redo works: before every change we take a "snapshot" (a copy of
    the strokes and template) and push it onto the undo stack. Undo pops the
    last snapshot back; redo does the opposite. Any new change empties the
    redo stack, just like in other drawing apps.
    """

    def __init__(self):
        self.strokes = []
        # Coloring templates were replaced by items in Round 3 (R7). Only
        # artwork saved in earlier rounds can still have one (see from_dict).
        self.template = None
        self._undo_stack = []
        self._redo_stack = []

    # ---- history helpers -------------------------------------------------

    def _snapshot(self):
        return {"strokes": copy.deepcopy(self.strokes), "template": self.template}

    def _restore(self, snapshot):
        self.strokes = snapshot["strokes"]
        self.template = snapshot["template"]

    def _remember_before_change(self):
        self._undo_stack.append(self._snapshot())
        self._redo_stack.clear()

    @property
    def can_undo(self):
        return len(self._undo_stack) > 0

    @property
    def can_redo(self):
        return len(self._redo_stack) > 0

    # ---- actions the user can take ---------------------------------------

    def add_stroke(self, tool, color, size, points):
        """Add a brush (R3) or eraser (R4) stroke. Returns the clean stroke."""
        stroke = make_stroke(tool, color, size, points)  # validate first
        self._remember_before_change()
        self.strokes.append(stroke)
        return stroke

    def place_item(self, item, color, size, x, y):
        """Place a shape, letter or number (R7) centered at (x, y).
        Returns its index in the list, so it can be selected."""
        new_item = make_item(item, color, size, x, y)  # validate first
        self._remember_before_change()
        self.strokes.append(new_item)
        return len(self.strokes) - 1

    def _check_item_index(self, index):
        """Raise ValueError unless there is a placed item at `index`."""
        is_index = not isinstance(index, bool) and isinstance(index, int)
        if not is_index or not 0 <= index < len(self.strokes) or self.strokes[index]["tool"] != "item":
            raise ValueError("There's no placed shape, letter or number there. Select one first.")

    def recolor_item(self, index, color):
        """Fill a placed item with a new color (R7). Undoable.

        Returns False (and does nothing) if it already has that color.
        """
        self._check_item_index(index)
        new_color = normalize_hex(color)
        if self.strokes[index]["color"] == new_color:
            return False
        self._remember_before_change()
        self.strokes[index]["color"] = new_color
        return True

    def rotate_item(self, index):
        """Turn a placed item a quarter turn (90 degrees) clockwise (R11). Undoable."""
        self._check_item_index(index)
        self._remember_before_change()
        item = self.strokes[index]
        item["rotation"] = (item["rotation"] + 90) % 360

    def flip_item(self, index, direction):
        """Mirror a placed item "horizontal"ly (left-right) or "vertical"ly
        (top-bottom), as it looks on screen right now (R11). Undoable.

        Why the rotation changes too: mirroring an item that is already turned
        is the same as mirroring it first and then turning it the other way.
        So we flip it and turn its rotation backwards. The R11 tests check
        that the result really is mirrored as seen on screen.
        """
        if direction not in FLIP_DIRECTIONS:
            raise ValueError("Flip must be 'horizontal' or 'vertical'.")
        self._check_item_index(index)
        self._remember_before_change()
        item = self.strokes[index]
        item["rotation"] = (360 - item["rotation"]) % 360
        side = "flip_x" if direction == "horizontal" else "flip_y"
        item[side] = not item[side]

    def item_at(self, x, y):
        """The index of the top placed item whose box contains (x, y), or None.
        Used by the Select tool (R7, R11)."""
        if not _is_number(x) or not _is_number(y):
            raise ValueError("A position needs two ordinary numbers.")
        for index in reversed(range(len(self.strokes))):  # top (newest) first
            mark = self.strokes[index]
            if mark["tool"] != "item":
                continue
            half = mark["size"] / 2
            if abs(x - mark["x"]) <= half and abs(y - mark["y"]) <= half:
                return index
        return None

    def clear(self):
        """Wipe the canvas completely (R8). Undo can bring it back.

        Returns False (and does nothing) if the canvas is already empty.
        """
        if not self.strokes and self.template is None:
            return False
        self._remember_before_change()
        self.strokes = []
        self.template = None
        return True

    def undo(self):
        """Step back one action (R5). Returns False if there's nothing to undo."""
        if not self.can_undo:
            return False
        self._redo_stack.append(self._snapshot())
        self._restore(self._undo_stack.pop())
        return True

    def redo(self):
        """Re-apply an undone action (R5). Returns False if there's nothing to redo."""
        if not self.can_redo:
            return False
        self._undo_stack.append(self._snapshot())
        self._restore(self._redo_stack.pop())
        return True

    # ---- converting to/from plain data (for saving, R6) ------------------

    def to_dict(self):
        """The artwork as plain data, ready to save as JSON."""
        return {"template": self.template, "strokes": copy.deepcopy(self.strokes)}

    def state(self):
        """Everything the browser needs to draw the canvas and its buttons."""
        data = self.to_dict()
        data["can_undo"] = self.can_undo
        data["can_redo"] = self.can_redo
        return data

    @classmethod
    def from_dict(cls, data):
        """Rebuild a Canvas from saved data. Every stroke and item is checked
        again, so a damaged save file raises ValueError instead of breaking
        the app. The reopened artwork starts with a fresh undo history.
        """
        if not isinstance(data, dict) or not isinstance(data.get("strokes"), list):
            raise ValueError("This artwork file is missing its strokes.")
        canvas = cls()
        for mark in data["strokes"]:
            if not isinstance(mark, dict):
                raise ValueError("This artwork file has a damaged stroke.")
            if mark.get("tool") == "item":
                canvas.strokes.append(make_item(
                    mark.get("item"), mark.get("color"), mark.get("size"), mark.get("x"), mark.get("y"),
                    mark.get("rotation"), mark.get("flip_x"), mark.get("flip_y"),
                ))
            else:
                canvas.strokes.append(
                    make_stroke(mark.get("tool"), mark.get("color"), mark.get("size"), mark.get("points"))
                )
        # Artwork saved before Round 3 may name a coloring template. It is
        # kept so the outline still shows (R7), but no new one can be chosen.
        template = data.get("template")
        if template is not None and not isinstance(template, str):
            raise ValueError("This artwork file has a damaged template name.")
        canvas.template = template
        return canvas
