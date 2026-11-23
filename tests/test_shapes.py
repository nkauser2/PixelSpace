"""Tests for shapes.py (R7: shapes, letters and numbers to place)."""

import pytest

from shapes import LETTERS, NUMBERS, SHAPE_OUTLINES, is_item, list_items


def test_r7_there_are_eight_shapes():
    """R7: The 8 agreed shapes are offered."""
    assert list(SHAPE_OUTLINES) == ["circle", "square", "triangle", "star", "heart", "diamond", "hexagon", "arrow"]


def test_r7_all_capital_letters_are_offered():
    """R7: Every capital letter A-Z can be placed."""
    assert LETTERS == list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def test_r7_all_digits_are_offered():
    """R7: Every digit 0-9 can be placed."""
    assert NUMBERS == list("0123456789")


def test_r7_item_list_has_every_item_once_with_id_name_and_kind():
    """R7: The menu lists 44 items (8 + 26 + 10), each with an id, name and kind."""
    items = list_items()
    assert len(items) == 44
    assert len({i["id"] for i in items}) == 44
    for item in items:
        assert set(item) == {"id", "name", "kind"}
        assert item["kind"] in ("shape", "letter", "number")
        assert item["name"]


def test_r7_item_kinds_are_correct():
    """R7: Shapes, letters and numbers are labelled with the right kind."""
    kinds = {i["id"]: i["kind"] for i in list_items()}
    assert kinds["heart"] == "shape"
    assert kinds["Q"] == "letter"
    assert kinds["7"] == "number"


@pytest.mark.parametrize("shape_id", list(SHAPE_OUTLINES))
def test_r7_every_shape_outline_fits_its_box(shape_id):
    """R7: Each shape outline has at least 3 corners and fits the 1 x 1 box."""
    points = SHAPE_OUTLINES[shape_id]
    assert len(points) >= 3
    for x, y in points:
        assert -0.5 <= x <= 0.5 and -0.5 <= y <= 0.5, (shape_id, x, y)


@pytest.mark.parametrize("item_id", ["circle", "arrow", "A", "Z", "0", "9"])
def test_r7_known_items_are_recognised(item_id):
    """R7: Real items are accepted."""
    assert is_item(item_id)


@pytest.mark.parametrize("item_id", ["a", "AB", "10", "dragon", "", None, 5, "cat"])
def test_r7_unknown_items_are_refused(item_id):
    """R7: Lowercase letters, old template names and junk aren't items."""
    assert not is_item(item_id)
