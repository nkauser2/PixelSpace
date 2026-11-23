"""Tests for the drawing logic in canvas_model.py.

Every test name starts with the requirement it checks, e.g. test_r3_...
"""

import math

import pytest

from canvas_model import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    MAX_ITEM_SIZE,
    MAX_SIZE,
    MIN_ITEM_SIZE,
    MIN_SIZE,
    Canvas,
    item_point_on_canvas,
    make_stroke,
)
from conftest import brush, eraser


def add(canvas, stroke):
    return canvas.add_stroke(stroke["tool"], stroke["color"], stroke["size"], stroke["points"])


def old_save(template="cat", color="#111111"):
    """A canvas opened from an earlier round's save that used a coloring template."""
    return Canvas.from_dict({"template": template, "strokes": [brush(color=color)]})


def place(canvas, item="star", color="#e63946", size=100, x=400, y=300):
    return canvas.place_item(item, color, size, x, y)


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
    canvas = old_save("cat")
    add(canvas, brush())
    add(canvas, eraser())
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


# ---------- R7: shapes, letters and numbers: see the end of this file ----------


# ---------- R8: clear canvas ----------

def test_r8_clear_removes_everything():
    """R8: Clear wipes all strokes and the template."""
    canvas = old_save("star")
    add(canvas, eraser())
    assert canvas.clear() is True
    assert canvas.strokes == []
    assert canvas.template is None


def test_r8_clear_can_be_undone():
    """R8: An accidental clear can be undone."""
    canvas = old_save("cat", color="#111111")
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


# ---------- R7: placing shapes, letters and numbers ----------

def test_r7_placing_an_item_adds_it_filled_with_the_color():
    """R7: A placed item keeps its name, fill color, size and position, and starts unturned."""
    canvas = Canvas()
    index = place(canvas, item="heart", color="#FF8FC7", size=150, x=200, y=120)
    assert index == 0
    assert canvas.strokes[0] == {
        "tool": "item", "item": "heart", "color": "#ff8fc7", "size": 150,
        "x": 200.0, "y": 120.0, "rotation": 0, "flip_x": False, "flip_y": False,
    }


@pytest.mark.parametrize("item", ["circle", "arrow", "A", "M", "0", "8"])
def test_r7_shapes_letters_and_numbers_can_all_be_placed(item):
    """R7: Shapes, letters and numbers can each be placed."""
    canvas = Canvas()
    place(canvas, item=item)
    assert canvas.strokes[0]["item"] == item


def test_r7_items_and_strokes_stay_in_the_order_they_were_added():
    """R7: Items are part of the drawing, so later brush strokes paint over them."""
    canvas = Canvas()
    add(canvas, brush())
    place(canvas)
    add(canvas, eraser())
    assert [s["tool"] for s in canvas.strokes] == ["brush", "item", "eraser"]


@pytest.mark.parametrize("item, color, size, x, y", [
    ("dragon", "#e63946", 100, 400, 300),       # not an item
    ("a", "#e63946", 100, 400, 300),            # lowercase letters aren't offered
    ("star", "red", 100, 400, 300),             # bad color
    ("star", None, 100, 400, 300),              # no color
    ("star", "#e63946", MIN_ITEM_SIZE - 1, 400, 300),
    ("star", "#e63946", MAX_ITEM_SIZE + 1, 400, 300),
    ("star", "#e63946", True, 400, 300),        # True is not a size
    ("star", "#e63946", "100", 400, 300),
    ("star", "#e63946", 100, -1, 300),          # off the canvas
    ("star", "#e63946", 100, 400, CANVAS_HEIGHT + 1),
    ("star", "#e63946", 100, math.nan, 300),
    ("star", "#e63946", 100, None, 300),
])
def test_r7_bad_items_are_refused_and_change_nothing(item, color, size, x, y):
    """R7: Invalid items give a clear error and the canvas stays the same."""
    canvas = Canvas()
    with pytest.raises(ValueError):
        canvas.place_item(item, color, size, x, y)
    assert canvas.strokes == []
    assert not canvas.can_undo


def test_r7_placing_an_item_can_be_undone_and_redone():
    """R7: Placing an item is one undo step, like a stroke."""
    canvas = Canvas()
    place(canvas)
    canvas.undo()
    assert canvas.strokes == []
    canvas.redo()
    assert canvas.strokes[0]["item"] == "star"


def test_r7_a_placed_item_can_be_recolored():
    """R7: Items are colorable: the selected item takes a newly picked color."""
    canvas = Canvas()
    index = place(canvas, color="#e63946")
    assert canvas.recolor_item(index, "#2F5BD3") is True
    assert canvas.strokes[index]["color"] == "#2f5bd3"


def test_r7_recoloring_can_be_undone_and_redone():
    """R7: Re-coloring an item is one undo step."""
    canvas = Canvas()
    index = place(canvas, color="#e63946")
    canvas.recolor_item(index, "#2f5bd3")
    canvas.undo()
    assert canvas.strokes[index]["color"] == "#e63946"
    canvas.redo()
    assert canvas.strokes[index]["color"] == "#2f5bd3"


def test_r7_recoloring_with_the_same_color_adds_no_undo_step():
    """R7: Picking the color an item already has changes nothing."""
    canvas = Canvas()
    index = place(canvas, color="#e63946")
    assert canvas.recolor_item(index, "#E63946") is False
    canvas.undo()
    assert canvas.strokes == []


@pytest.mark.parametrize("index", [0, 5, -1, None, "1", True])
def test_r7_recoloring_something_that_is_not_an_item_is_refused(index):
    """R7: Only placed items can be re-colored (index 0 here is a brush stroke)."""
    canvas = Canvas()
    add(canvas, brush(color="#111111"))
    place(canvas)
    with pytest.raises(ValueError):
        canvas.recolor_item(index, "#2f5bd3")
    assert canvas.strokes[0]["color"] == "#111111"
    assert canvas.strokes[1]["color"] == "#e63946"


def test_r7_recoloring_with_a_bad_color_is_refused():
    """R7: A bad color leaves the item as it was."""
    canvas = Canvas()
    index = place(canvas, color="#e63946")
    with pytest.raises(ValueError):
        canvas.recolor_item(index, "blue")
    assert canvas.strokes[index]["color"] == "#e63946"
    canvas.undo()
    assert canvas.strokes == []


def test_r7_clicking_an_item_finds_it():
    """R7: The Select tool finds the item under the pointer."""
    canvas = Canvas()
    place(canvas, size=100, x=400, y=300)
    assert canvas.item_at(400, 300) == 0
    assert canvas.item_at(449, 349) == 0  # just inside its box
    assert canvas.item_at(451, 300) is None  # just outside


def test_r7_clicking_overlapping_items_finds_the_top_one():
    """R7: When items overlap, the one placed last (on top) is found."""
    canvas = Canvas()
    place(canvas, x=400, y=300)
    place(canvas, x=420, y=300)
    assert canvas.item_at(410, 300) == 1


def test_r7_clicking_a_brush_stroke_finds_no_item():
    """R7: Brush strokes can't be selected, only items."""
    canvas = Canvas()
    add(canvas, brush(points=[[10, 10], [20, 20]]))
    assert canvas.item_at(15, 15) is None


@pytest.mark.parametrize("x, y", [(None, 1), ("1", 1), (True, 1), (math.inf, 1)])
def test_r7_finding_an_item_needs_real_numbers(x, y):
    """R7: A bad click position gives a clear error."""
    with pytest.raises(ValueError):
        Canvas().item_at(x, y)


def test_r7_old_save_with_a_template_still_opens_with_its_outline():
    """R7: Artwork saved with a template in an earlier round still opens and keeps it."""
    canvas = old_save("house")
    assert canvas.template == "house"
    assert canvas.to_dict()["template"] == "house"  # saving it again keeps it


def test_r7_canvas_has_no_way_to_choose_a_new_template():
    """R7: Templates are replaced, so a template can't be chosen any more."""
    assert not hasattr(Canvas(), "set_template")


def test_r6_placed_items_are_saved_and_reopened():
    """R6: Items (with their color, flips and rotation) come back when reopened."""
    canvas = Canvas()
    add(canvas, brush())
    index = place(canvas, item="A")
    canvas.rotate_item(index)
    canvas.flip_item(index, "vertical")
    reopened = Canvas.from_dict(canvas.to_dict())
    assert reopened.strokes == canvas.strokes


@pytest.mark.parametrize("bad_field", [
    {"item": "dragon"},
    {"color": "nope"},
    {"size": 9999},
    {"rotation": 45},
    {"rotation": True},
    {"flip_x": "yes"},
    {"x": None},
])
def test_r6_damaged_item_in_a_save_is_rejected(bad_field):
    """R6: A save file with a damaged item gives a clear error."""
    good = {"tool": "item", "item": "star", "color": "#e63946", "size": 100,
            "x": 400, "y": 300, "rotation": 0, "flip_x": False, "flip_y": False}
    with pytest.raises(ValueError):
        Canvas.from_dict({"strokes": [{**good, **bad_field}]})


def test_r8_clear_removes_placed_items():
    """R8: Clear removes items too, and undo brings them back."""
    canvas = Canvas()
    place(canvas)
    assert canvas.clear() is True
    assert canvas.strokes == []
    canvas.undo()
    assert canvas.strokes[0]["item"] == "star"


# ---------- R11: flip and rotate ----------

def screen_point(item, local_x, local_y):
    """Where a point of the item's box shows up, relative to the item's center."""
    x, y = item_point_on_canvas(item, local_x, local_y)
    return (round(x - item["x"], 6), round(y - item["y"], 6))


# A few different starting states, so flips are checked after rotating too.
STARTING_TURNS = [
    [],
    ["rotate"],
    ["rotate", "rotate"],
    ["rotate", "rotate", "rotate"],
    ["horizontal"],
    ["vertical", "rotate"],
]


def turned_item(turns):
    canvas = Canvas()
    index = place(canvas, item="F", size=100, x=400, y=300)
    for turn in turns:
        if turn == "rotate":
            canvas.rotate_item(index)
        else:
            canvas.flip_item(index, turn)
    return canvas, index


def test_r11_each_rotate_click_turns_90_degrees():
    """R11: Each click rotates the item another 90 degrees."""
    canvas = Canvas()
    index = place(canvas)
    angles = []
    for _ in range(4):
        canvas.rotate_item(index)
        angles.append(canvas.strokes[index]["rotation"])
    assert angles == [90, 180, 270, 0]


def test_r11_rotating_turns_the_item_clockwise():
    """R11: The top of the item moves to the right side, as seen on screen."""
    canvas = Canvas()
    index = place(canvas, size=100)
    canvas.rotate_item(index)
    # The middle of the top edge (0, -0.5) is now in the middle of the right edge.
    assert screen_point(canvas.strokes[index], 0, -0.5) == pytest.approx((50, 0))


@pytest.mark.parametrize("turns", STARTING_TURNS)
def test_r11_rotating_always_turns_clockwise_on_screen(turns):
    """R11: Rotate turns clockwise as seen on screen, even after flips."""
    canvas, index = turned_item(turns)
    before = screen_point(canvas.strokes[index], 0.3, -0.2)
    canvas.rotate_item(index)
    after = screen_point(canvas.strokes[index], 0.3, -0.2)
    # Turning (x, y) a quarter turn clockwise (y grows downwards) gives (-y, x).
    assert after == pytest.approx((-before[1], before[0]))


@pytest.mark.parametrize("turns", STARTING_TURNS)
def test_r11_flip_horizontal_mirrors_left_and_right_on_screen(turns):
    """R11: Flip left-right swaps left and right as seen now, even if the item is rotated."""
    canvas, index = turned_item(turns)
    before = screen_point(canvas.strokes[index], 0.3, -0.2)
    canvas.flip_item(index, "horizontal")
    after = screen_point(canvas.strokes[index], 0.3, -0.2)
    assert after == pytest.approx((-before[0], before[1]))


@pytest.mark.parametrize("turns", STARTING_TURNS)
def test_r11_flip_vertical_mirrors_top_and_bottom_on_screen(turns):
    """R11: Flip top-bottom swaps top and bottom as seen now, even if the item is rotated."""
    canvas, index = turned_item(turns)
    before = screen_point(canvas.strokes[index], 0.3, -0.2)
    canvas.flip_item(index, "vertical")
    after = screen_point(canvas.strokes[index], 0.3, -0.2)
    assert after == pytest.approx((before[0], -before[1]))


@pytest.mark.parametrize("direction", ["horizontal", "vertical"])
def test_r11_flipping_twice_puts_the_item_back(direction):
    """R11: Two flips the same way bring the item back to how it was."""
    canvas, index = turned_item(["rotate"])
    original = dict(canvas.strokes[index])
    canvas.flip_item(index, direction)
    assert canvas.strokes[index] != original
    canvas.flip_item(index, direction)
    assert canvas.strokes[index] == original


def test_r11_four_rotations_put_the_item_back():
    """R11: Four quarter turns make a full turn."""
    canvas, index = turned_item(["horizontal"])
    original = dict(canvas.strokes[index])
    for _ in range(4):
        canvas.rotate_item(index)
    assert canvas.strokes[index] == original


@pytest.mark.parametrize("turns", STARTING_TURNS + [["rotate", "horizontal", "vertical"]])
def test_r11_flips_and_turns_keep_the_item_in_place(turns):
    """R11: Items turn around their own center, and keep their color and size."""
    canvas, index = turned_item(turns)
    item = canvas.strokes[index]
    assert item_point_on_canvas(item, 0, 0) == pytest.approx((400, 300))
    assert (item["x"], item["y"], item["size"], item["color"]) == (400, 300, 100, "#e63946")


@pytest.mark.parametrize("action", ["rotate", "horizontal", "vertical"])
def test_r11_each_flip_or_rotate_can_be_undone_and_redone(action):
    """R11: Every click is its own undo step."""
    canvas, index = turned_item([])
    original = dict(canvas.strokes[index])
    turned = turned_item([action])[0].strokes[index]

    if action == "rotate":
        canvas.rotate_item(index)
    else:
        canvas.flip_item(index, action)
    canvas.undo()
    assert canvas.strokes[index] == original
    canvas.redo()
    assert canvas.strokes[index] == turned


@pytest.mark.parametrize("index", [0, 9, None, "1"])
def test_r11_flip_and_rotate_only_work_on_placed_items(index):
    """R11: Trying to flip or rotate a brush stroke or a missing item is refused."""
    canvas = Canvas()
    add(canvas, brush())
    place(canvas)
    with pytest.raises(ValueError):
        canvas.rotate_item(index)
    with pytest.raises(ValueError):
        canvas.flip_item(index, "horizontal")
    assert canvas.strokes[1]["rotation"] == 0
    assert not canvas.strokes[1]["flip_x"]


@pytest.mark.parametrize("direction", ["diagonal", "", None, "Horizontal"])
def test_r11_unknown_flip_direction_is_refused(direction):
    """R11: Only horizontal and vertical flips exist."""
    canvas = Canvas()
    index = place(canvas)
    with pytest.raises(ValueError):
        canvas.flip_item(index, direction)
    assert not canvas.strokes[index]["flip_x"] and not canvas.strokes[index]["flip_y"]
    canvas.undo()
    assert canvas.strokes == []
