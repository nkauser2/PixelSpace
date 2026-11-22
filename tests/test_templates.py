"""Tests for coloring_templates.py (R7: ready-made coloring templates)."""

import pytest

from canvas_model import CANVAS_HEIGHT, CANVAS_WIDTH
from coloring_templates import TEMPLATES, get_template, list_templates

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


def test_r7_there_are_several_templates_to_choose_from():
    """R7: PixelSpace offers at least a few ready-made templates."""
    assert len(list_templates()) >= 3


def test_r7_template_list_has_ids_and_names():
    """R7: Each template in the menu has an id and a display name."""
    for item in list_templates():
        assert set(item) == {"id", "name"}
        assert item["id"] and item["name"]


def test_r7_ids_are_unique():
    """R7: No two templates share an id."""
    ids = [t["id"] for t in list_templates()]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("template_id", list(TEMPLATES))
def test_r7_every_template_has_valid_shapes(template_id):
    """R7: Every template is made of known shapes with all their fields."""
    template = get_template(template_id)
    assert template["shapes"], "a template must have at least one shape"
    for shape in template["shapes"]:
        assert shape["type"] in SHAPE_FIELDS, shape
        assert SHAPE_FIELDS[shape["type"]] <= set(shape), shape
        if shape["type"] in ("line", "polygon"):
            assert len(shape["points"]) >= 2


@pytest.mark.parametrize("template_id", list(TEMPLATES))
def test_r7_every_template_fits_on_the_canvas(template_id):
    """R7: No part of any template is drawn off the edge of the canvas."""
    for shape in get_template(template_id)["shapes"]:
        for x, y in all_points(shape):
            assert 0 <= x <= CANVAS_WIDTH and 0 <= y <= CANVAS_HEIGHT, (template_id, shape)


def test_r7_unknown_template_returns_none():
    """R7: Asking for a template that doesn't exist returns None."""
    assert get_template("dragon-that-does-not-exist") is None
