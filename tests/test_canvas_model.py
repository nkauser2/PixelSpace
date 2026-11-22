"""Tests for the drawing logic in canvas_model.py.

Every test name starts with the requirement it checks, e.g. test_r3_...
"""

import math

import pytest

from canvas_model import CANVAS_HEIGHT, CANVAS_WIDTH, MAX_SIZE, MIN_SIZE, Canvas, make_stroke
from conftest import brush, eraser


def add(canvas, stroke):
    return canvas.add_stroke(stroke["tool"], stroke["color"], stroke["size"], stroke["points"])


# ---------- R1: an interactive canvas ----------

def test_r1_new_canvas_starts_empty():
    """R1: A new canvas is blank and ready to draw on."""
    canvas = Canvas()
    assert canvas.strokes == []
    assert canvas.template is None
    assert not canvas.can_undo and not canvas.can_redo


def test_r1_canvas_has_a_sensible_size():
    """R1: The drawing area has a fixed, landscape size."""
    assert CANVAS_WIDTH == 800
    assert CANVAS_HEIGHT == 600


def test_r1_state_has_everything_the_page_needs():
    """R1: The state sent to the browser includes strokes, template and button states."""
    state = Canvas().state()
    assert set(state) == {"strokes", "template", "can_undo", "can_redo"}


# ---------- R2: color selection on strokes ----------

def test_r2_brush_stroke_keeps_the_chosen_color():
    """R2: A brush stroke is drawn in the color the user picked."""
    canvas = Canvas()
    add(canvas, brush(color="#2f5bd3"))
    assert canvas.strokes[0]["color"] == "#2f5bd3"


def test_r2_custom_color_is_normalized():
    """R2: Custom colors in any valid form are stored the same way."""
    stroke = make_stroke("brush", "#ABC", 5, [[1, 1]])
    assert stroke["color"] == "#aabbcc"


@pytest.mark.parametrize("bad_color", ["red", "#12345g", "", None, "#1234", 123])
def test_r2_brush_rejects_invalid_colors(bad_color):
    """R2: A brush stroke with an invalid color is refused."""
    with pytest.raises(ValueError):
        make_stroke("brush", bad_color, 5, [[1, 1]])


# ---------- R3: freehand brush ----------

def test_r3_brush_stroke_is_added():
    """R3: Drawing with the brush adds a stroke with its points and size."""
    canvas = Canvas()
    add(canvas, brush(points=[[0, 0], [5, 5], [10, 3]], size=12))
    assert len(canvas.strokes) == 1
    stroke = canvas.strokes[0]
    assert stroke["tool"] == "brush"
    assert stroke["size"] == 12
    assert stroke["points"] == [[0.0, 0.0], [5.0, 5.0], [10.0, 3.0]]


def test_r3_single_click_makes_a_dot():
    """R3: A stroke with only one point (a click) is allowed."""
    canvas = Canvas()
    add(canvas, brush(points=[[50, 50]]))
    assert canvas.strokes[0]["points"] == [[50.0, 50.0]]


def test_r3_strokes_stay_in_drawing_order():
    """R3: Strokes are kept in the order they were drawn."""
    canvas = Canvas()
    add(canvas, brush(color="#111111"))
    add(canvas, brush(color="#222222"))
    assert [s["color"] for s in canvas.strokes] == ["#111111", "#222222"]


def test_r3_points_are_rounded_to_keep_files_small():
    """R3: Point coordinates are rounded to one decimal place."""
    stroke = make_stroke("brush", "#000000", 5, [[1.23456, 9.87654]])
    assert stroke["points"] == [[1.2, 9.9]]


@pytest.mark.parametrize("size", [MIN_SIZE, MAX_SIZE, 7.5])
def test_r3_brush_sizes_in_range_are_accepted(size):
    """R3: Any brush size from the minimum to the maximum works."""
    assert make_stroke("brush", "#000000", size, [[1, 1]])["size"] == size


@pytest.mark.parametrize("size", [0, MAX_SIZE + 1, -5, "big", None, True])
def test_r3_bad_brush_sizes_are_rejected(size):
    """R3: Sizes that are too small, too large, or not numbers are refused."""
    with pytest.raises(ValueError):
        make_stroke("brush", "#000000", size, [[1, 1]])


@pytest.mark.parametrize("points", [[], None, "abc", [[1]], [[1, 2, 3]], [["a", 2]], [[math.nan, 1]], [[1, math.inf]]])
def test_r3_bad_points_are_rejected(points):
    """R3: Strokes with missing or broken points are refused."""
    with pytest.raises(ValueError):
        make_stroke("brush", "#000000", 5, points)


def test_r3_unknown_tool_is_rejected():
    """R3: Only real tools (brush/eraser) can make strokes."""
    with pytest.raises(ValueError):
        make_stroke("spray-can", "#000000", 5, [[1, 1]])


def test_r3_rejected_stroke_changes_nothing():
    """R3: A refused stroke doesn't change the drawing or the undo history."""
    canvas = Canvas()
    with pytest.raises(ValueError):
        canvas.add_stroke("brush", "not-a-color", 5, [[1, 1]])
    assert canvas.strokes == []
    assert not canvas.can_undo


# ---------- R4: eraser ----------

def test_r4_eraser_stroke_is_added():
    """R4: Using the eraser adds an eraser stroke on top of the drawing."""
    canvas = Canvas()
    add(canvas, brush())
    add(canvas, eraser(size=30))
    assert [s["tool"] for s in canvas.strokes] == ["brush", "eraser"]
    assert canvas.strokes[1]["size"] == 30


def test_r4_eraser_does_not_need_a_color():
    """R4: The eraser ignores any color it's given."""
    stroke = make_stroke("eraser", "#ff0000", 10, [[1, 1]])
    assert stroke["color"] is None
    assert make_stroke("eraser", None, 10, [[1, 1]])["color"] is None


def test_r4_erasing_can_be_undone():
    """R4: An eraser mistake can be undone, bringing the paint back."""
    canvas = Canvas()
    add(canvas, brush())
    add(canvas, eraser())
    canvas.undo()
    assert [s["tool"] for s in canvas.strokes] == ["brush"]


# ---------- R5: undo / redo ----------

def test_r5_undo_removes_the_last_stroke():
    """R5: Undo takes away the most recent stroke."""
    canvas = Canvas()
    add(canvas, brush(color="#111111"))
    add(canvas, brush(color="#222222"))
    assert canvas.undo() is True
    assert [s["color"] for s in canvas.strokes] == ["#111111"]


def test_r5_redo_brings_the_stroke_back():
    """R5: Redo puts back what undo removed."""
    canvas = Canvas()
    add(canvas, brush(color="#111111"))
    canvas.undo()
    assert canvas.redo() is True
    assert [s["color"] for s in canvas.strokes] == ["#111111"]


def test_r5_several_undos_then_redos_keep_the_right_order():
    """R5: Undoing and redoing several steps happens in the right order."""
    canvas = Canvas()
    for c in ["#111111", "#222222", "#333333"]:
        add(canvas, brush(color=c))
    canvas.undo()
    canvas.undo()
    assert [s["color"] for s in canvas.strokes] == ["#111111"]
    canvas.redo()
    assert [s["color"] for s in canvas.strokes] == ["#111111", "#222222"]
    canvas.redo()
    assert [s["color"] for s in canvas.strokes] == ["#111111", "#222222", "#333333"]


def test_r5_new_stroke_clears_redo():
    """R5: Drawing something new after undo means the old redo is gone."""
    canvas = Canvas()
    add(canvas, brush(color="#111111"))
    canvas.undo()
    add(canvas, brush(color="#999999"))
    assert not canvas.can_redo
    assert canvas.redo() is False
    assert [s["color"] for s in canvas.strokes] == ["#999999"]


def test_r5_undo_and_redo_do_nothing_when_history_is_empty():
    """R5: Pressing undo/redo with nothing to undo/redo is safe."""
    canvas = Canvas()
    assert canvas.undo() is False
    assert canvas.redo() is False
    assert canvas.strokes == []


def test_r5_button_flags_follow_the_history():
    """R5: can_undo / can_redo tell the page when to enable the buttons."""
    canvas = Canvas()
    add(canvas, brush())
    assert canvas.can_undo and not canvas.can_redo
    canvas.undo()
    assert not canvas.can_undo and canvas.can_redo


def test_r5_undo_does_not_change_earlier_strokes():
    """R5: Undo restores an exact copy, even if a stroke object was changed later."""
    canvas = Canvas()
    add(canvas, brush(points=[[1, 1]]))
    add(canvas, brush(points=[[2, 2]]))
    canvas.strokes[0]["points"].append([99, 99])  # simulate accidental change
    canvas.undo()
    assert canvas.strokes[0]["points"] == [[1.0, 1.0]]


# ---------- R6: data for saving and reopening ----------

def test_r6_artwork_round_trips_through_plain_data():
    """R6: A canvas turned into data and back looks exactly the same."""
    canvas = Canvas()
    add(canvas, brush())
    add(canvas, eraser())
    canvas.set_template("cat")
    copy = Canvas.from_dict(canvas.to_dict())
    assert copy.strokes == canvas.strokes
    assert copy.template == "cat"


def test_r6_reopened_artwork_starts_with_fresh_history():
    """R6: A reopened artwork can be drawn on, but has no old undo steps."""
    canvas = Canvas()
    add(canvas, brush())
    reopened = Canvas.from_dict(canvas.to_dict())
    assert not reopened.can_undo and not reopened.can_redo


@pytest.mark.parametrize("data", [
    None,
    "text",
    {},
    {"strokes": "nope"},
    {"strokes": ["nope"]},
    {"strokes": [{"tool": "brush", "color": "bad", "size": 5, "points": [[1, 1]]}]},
    {"strokes": [], "template": 42},
])
def test_r6_damaged_artwork_data_is_rejected(data):
    """R6: Damaged saved data gives a clear error instead of crashing."""
    with pytest.raises(ValueError):
        Canvas.from_dict(data)


# ---------- R7: templates on the canvas ----------

def test_r7_choosing_a_template_shows_it():
    """R7: Picking a coloring template puts it on the canvas."""
    canvas = Canvas()
    assert canvas.set_template("flower") is True
    assert canvas.template == "flower"


def test_r7_choosing_the_same_template_again_does_nothing():
    """R7: Re-picking the current template doesn't add an undo step."""
    canvas = Canvas()
    canvas.set_template("flower")
    assert canvas.set_template("flower") is False
    canvas.undo()
    assert canvas.template is None


def test_r7_template_change_can_be_undone_and_keeps_strokes():
    """R7: Switching templates is undoable and doesn't erase your coloring."""
    canvas = Canvas()
    canvas.set_template("house")
    add(canvas, brush())
    canvas.set_template("fish")
    assert len(canvas.strokes) == 1
    canvas.undo()
    assert canvas.template == "house"
    assert len(canvas.strokes) == 1


# ---------- R8: clear canvas ----------

def test_r8_clear_removes_everything():
    """R8: Clear wipes all strokes and the template."""
    canvas = Canvas()
    add(canvas, brush())
    add(canvas, eraser())
    canvas.set_template("star")
    assert canvas.clear() is True
    assert canvas.strokes == []
    assert canvas.template is None


def test_r8_clear_can_be_undone():
    """R8: An accidental clear can be undone."""
    canvas = Canvas()
    add(canvas, brush(color="#111111"))
    canvas.set_template("cat")
    canvas.clear()
    canvas.undo()
    assert [s["color"] for s in canvas.strokes] == ["#111111"]
    assert canvas.template == "cat"


def test_r8_clear_can_be_redone():
    """R8: After undoing a clear, redo clears again."""
    canvas = Canvas()
    add(canvas, brush())
    canvas.clear()
    canvas.undo()
    canvas.redo()
    assert canvas.strokes == []


def test_r8_clearing_an_empty_canvas_does_nothing():
    """R8: Clearing a blank canvas doesn't add a pointless undo step."""
    canvas = Canvas()
    assert canvas.clear() is False
    assert not canvas.can_undo
