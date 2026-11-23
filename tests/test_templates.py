"""Tests for coloring_templates.py (R7: template outlines that artwork saved
before Round 3 still shows when it is opened)."""

import pytest

from canvas_model import CANVAS_HEIGHT, CANVAS_WIDTH
from coloring_templates import TEMPLATES, get_template

SHAPE_FIELDS = {
    "circle": {"cx", "cy", "r"},
    "ellipse": {"cx", "cy", "rx", "ry", "rotation"},
    "rect": {"x", "y", "w", "h"},
    "line": {"points"},
    "polygon": {"points"},
}


def all_points(shape):
    """The key x/y positions of a shape, used to check it's on the canvas."""
    t = shape["type"]
    if t == "circle":
        return [(shape["cx"] - shape["r"], shape["cy"] - shape["r"]), (shape["cx"] + shape["r"], shape["cy"] + shape["r"])]
    if t == "ellipse":
        big = max(shape["rx"], shape["ry"])
        return [(shape["cx"] - big, shape["cy"] - big), (shape["cx"] + big, shape["cy"] + big)]
    if t == "rect":
        return [(shape["x"], shape["y"]), (shape["x"] + shape["w"], shape["y"] + shape["h"])]
    return [tuple(p) for p in shape["points"]]


def test_r7_every_template_an_old_save_can_name_is_still_there():
    """R7: All five Round 1 templates can still be drawn for old saves."""
    assert set(TEMPLATES) == {"flower", "house", "cat", "fish", "star"}


@pytest.mark.parametrize("template_id", list(TEMPLATES))
def test_r7_every_template_has_valid_shapes(template_id):
    """R7: Every old template outline is made of known shapes with all their fields."""
    template = get_template(template_id)
    assert template["shapes"], "a template must have at least one shape"
    for shape in template["shapes"]:
        assert shape["type"] in SHAPE_FIELDS, shape
        assert SHAPE_FIELDS[shape["type"]] <= set(shape), shape
        if shape["type"] in ("line", "polygon"):
            assert len(shape["points"]) >= 2


@pytest.mark.parametrize("template_id", list(TEMPLATES))
def test_r7_every_template_fits_on_the_canvas(template_id):
    """R7: No part of any old template outline is drawn off the edge of the canvas."""
    for shape in get_template(template_id)["shapes"]:
        for x, y in all_points(shape):
            assert 0 <= x <= CANVAS_WIDTH and 0 <= y <= CANVAS_HEIGHT, (template_id, shape)


def test_r7_unknown_template_returns_none():
    """R7: Asking for a template that doesn't exist returns None."""
    assert get_template("dragon-that-does-not-exist") is None
