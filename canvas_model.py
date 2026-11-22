"""The drawing document for PixelSpace.

The browser draws on the screen, but the artwork itself is stored here as a
list of strokes. Keeping it in Python lets us test drawing (R3), erasing (R4),
undo/redo (R5), templates (R7) and clearing (R8) without a browser.

A stroke is a dictionary like:
    {"tool": "brush", "color": "#e63946", "size": 8, "points": [[10, 20], [12, 24]]}
"""

import copy
import math

from colors import normalize_hex

CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600

TOOLS = ("brush", "eraser")
MIN_SIZE = 1
MAX_SIZE = 100
MAX_POINTS = 10_000  # stops one stroke from being absurdly large


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
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError("Point coordinates must be ordinary numbers.")
        clean_points.append([round(float(x), 1), round(float(y), 1)])

    return {"tool": tool, "color": clean_color, "size": size, "points": clean_points}


class Canvas:
    """One piece of artwork: its strokes, its template, and its undo/redo history.

    How undo/redo works: before every change we take a "snapshot" (a copy of
    the strokes and template) and push it onto the undo stack. Undo pops the
    last snapshot back; redo does the opposite. Any new change empties the
    redo stack, just like in other drawing apps.
    """

    def __init__(self):
        self.strokes = []
        self.template = None  # id of a coloring template, or None
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

    def set_template(self, template_id):
        """Show a coloring template (R7), or None to remove it. Undoable."""
        if template_id == self.template:
            return False
        self._remember_before_change()
        self.template = template_id
        return True

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
        """Rebuild a Canvas from saved data. Every stroke is checked again,
        so a damaged save file raises ValueError instead of breaking the app.
        The reopened artwork starts with a fresh undo history.
        """
        if not isinstance(data, dict) or not isinstance(data.get("strokes"), list):
            raise ValueError("This artwork file is missing its strokes.")
        canvas = cls()
        for stroke in data["strokes"]:
            if not isinstance(stroke, dict):
                raise ValueError("This artwork file has a damaged stroke.")
            canvas.strokes.append(
                make_stroke(stroke.get("tool"), stroke.get("color"), stroke.get("size"), stroke.get("points"))
            )
        template = data.get("template")
        if template is not None and not isinstance(template, str):
            raise ValueError("This artwork file has a damaged template name.")
        canvas.template = template
        return canvas
