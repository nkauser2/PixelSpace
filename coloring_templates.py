"""Ready-made coloring templates (R7).

Each template is a list of simple outline shapes that the browser draws on
top of the user's paint, so coloring always stays "under the lines" and the
eraser can't remove the outlines.

Shape types (all coordinates are on the 800 x 600 canvas):
    circle   {"cx", "cy", "r"}
    ellipse  {"cx", "cy", "rx", "ry", "rotation"}   rotation is in degrees
    rect     {"x", "y", "w", "h"}
    line     {"points": [[x, y], ...]}   an open path
    polygon  {"points": [[x, y], ...]}   a closed shape
"""

import math


def _flower():
    shapes = []
    # Eight petals arranged in a ring around the center.
    for i in range(8):
        angle = i * 45
        rad = math.radians(angle)
        shapes.append({
            "type": "ellipse",
            "cx": round(400 + 80 * math.cos(rad), 1),
            "cy": round(250 + 80 * math.sin(rad), 1),
            "rx": 55, "ry": 28, "rotation": angle,
        })
    shapes += [
        {"type": "circle", "cx": 400, "cy": 250, "r": 38},
        {"type": "line", "points": [[400, 358], [400, 560]]},  # stem
        {"type": "ellipse", "cx": 445, "cy": 465, "rx": 45, "ry": 18, "rotation": -30},
        {"type": "ellipse", "cx": 355, "cy": 505, "rx": 45, "ry": 18, "rotation": 30},
        {"type": "line", "points": [[150, 560], [650, 560]]},  # ground
    ]
    return shapes


def _house():
    return [
        {"type": "rect", "x": 250, "y": 280, "w": 300, "h": 240},          # walls
        {"type": "polygon", "points": [[230, 280], [400, 150], [570, 280]]},  # roof
        {"type": "line", "points": [[480, 211], [480, 165], [520, 165], [520, 242]]},  # chimney
        {"type": "rect", "x": 370, "y": 400, "w": 60, "h": 120},           # door
        {"type": "circle", "cx": 418, "cy": 462, "r": 5},                   # door knob
        {"type": "rect", "x": 280, "y": 320, "w": 60, "h": 60},            # left window
        {"type": "line", "points": [[310, 320], [310, 380]]},
        {"type": "line", "points": [[280, 350], [340, 350]]},
        {"type": "rect", "x": 460, "y": 320, "w": 60, "h": 60},            # right window
        {"type": "line", "points": [[490, 320], [490, 380]]},
        {"type": "line", "points": [[460, 350], [520, 350]]},
        {"type": "circle", "cx": 680, "cy": 100, "r": 45},                  # sun
        {"type": "line", "points": [[80, 520], [720, 520]]},               # ground
    ]


def _cat():
    return [
        {"type": "ellipse", "cx": 400, "cy": 480, "rx": 120, "ry": 95, "rotation": 0},  # body
        {"type": "circle", "cx": 400, "cy": 260, "r": 110},                              # head
        {"type": "polygon", "points": [[315, 195], [320, 100], [380, 155]]},             # ears
        {"type": "polygon", "points": [[485, 195], [480, 100], [420, 155]]},
        {"type": "ellipse", "cx": 360, "cy": 245, "rx": 18, "ry": 24, "rotation": 0},   # eyes
        {"type": "ellipse", "cx": 440, "cy": 245, "rx": 18, "ry": 24, "rotation": 0},
        {"type": "polygon", "points": [[390, 290], [410, 290], [400, 302]]},             # nose
        {"type": "line", "points": [[400, 302], [400, 315]]},
        {"type": "line", "points": [[380, 325], [400, 315], [420, 325]]},                # mouth
        {"type": "line", "points": [[370, 300], [300, 290]]},                            # whiskers
        {"type": "line", "points": [[370, 310], [300, 315]]},
        {"type": "line", "points": [[430, 300], [500, 290]]},
        {"type": "line", "points": [[430, 310], [500, 315]]},
    ]


def _fish():
    return [
        {"type": "ellipse", "cx": 380, "cy": 300, "rx": 170, "ry": 100, "rotation": 0},  # body
        {"type": "polygon", "points": [[540, 300], [660, 210], [660, 390]]},             # tail
        {"type": "polygon", "points": [[360, 205], [420, 150], [450, 215]]},             # fin
        {"type": "circle", "cx": 290, "cy": 275, "r": 14},                                # eye
        {"type": "line", "points": [[380, 205], [395, 300], [380, 395]]},                 # stripes
        {"type": "line", "points": [[450, 212], [462, 300], [450, 388]]},
        {"type": "circle", "cx": 200, "cy": 150, "r": 12},                                # bubbles
        {"type": "circle", "cx": 170, "cy": 100, "r": 8},
        {"type": "circle", "cx": 215, "cy": 60, "r": 6},
    ]


def _star():
    points = []
    for i in range(10):  # alternate between outer and inner corners
        radius = 220 if i % 2 == 0 else 90
        rad = math.radians(-90 + i * 36)
        points.append([round(400 + radius * math.cos(rad), 1), round(320 + radius * math.sin(rad), 1)])
    return [{"type": "polygon", "points": points}]


# id -> (display name, shapes)
TEMPLATES = {
    "flower": ("Flower", _flower()),
    "house": ("House", _house()),
    "cat": ("Cat", _cat()),
    "fish": ("Fish", _fish()),
    "star": ("Star", _star()),
}


def list_templates():
    """A short list of templates for the menu: [{"id": ..., "name": ...}, ...]."""
    return [{"id": tid, "name": name} for tid, (name, _shapes) in TEMPLATES.items()]


def get_template(template_id):
    """Full template data, or None if there's no template with that id."""
    if template_id not in TEMPLATES:
        return None
    name, shapes = TEMPLATES[template_id]
    return {"id": template_id, "name": name, "shapes": shapes}
