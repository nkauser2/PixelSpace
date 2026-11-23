"""End-to-end tests of the web app using Flask's test client.

These act like the browser: they send the same requests the page sends.
They save into a temporary folder, never the real saves/ folder.
"""

import json

import storage
from colors import PALETTE
from conftest import brush, eraser
from shapes import list_items


def item(name="star", color="#e63946", size=100, x=400, y=300):
    """A ready-made "place this item" request (R7)."""
    return {"item": name, "color": color, "size": size, "x": x, "y": y}


def write_old_save(save_dir, name, template):
    """Write a save file the way Rounds 1-2 did, when templates still existed."""
    save_dir.mkdir(parents=True, exist_ok=True)
    data = {"app": "PixelSpace", "version": 1, "name": name, "saved_at": "2026-10-01T10:00:00",
            "template": template, "strokes": [brush(color="#2a9d5c")]}
    path = save_dir / f"{name}.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# ---------- R1: interactive canvas ----------

def test_r1_home_page_shows_the_canvas(client):
    """R1: Opening PixelSpace shows the drawing canvas and toolbar."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'id="paint-layer"' in html
    assert 'id="template-layer"' in html
    assert "PixelSpace" in html
    assert "app.js" in html


def test_r1_starting_state_is_a_blank_canvas(client):
    """R1: The canvas starts blank with undo/redo turned off."""
    state = client.get("/api/state").get_json()
    assert state == {"strokes": [], "template": None, "can_undo": False, "can_redo": False}


def test_r1_page_script_and_styles_are_served(client):
    """R1: The browser can load the drawing script and styles."""
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/style.css").status_code == 200


# ---------- R2: colors ----------

def test_r2_page_shows_every_palette_color(client):
    """R2: Every palette color appears as a swatch on the page."""
    html = client.get("/").get_data(as_text=True)
    for color in PALETTE:
        assert f'data-color="{color["hex"]}"' in html


def test_r2_page_has_a_custom_color_picker(client):
    """R2: There's a custom color picker on the page."""
    html = client.get("/").get_data(as_text=True)
    assert 'type="color"' in html


def test_r2_palette_api_returns_the_palette(client):
    """R2: The palette is also available as JSON."""
    assert client.get("/api/palette").get_json() == PALETTE


def test_r2_custom_color_stroke_is_accepted(client):
    """R2: A stroke in a custom color (not from the palette) works."""
    state = client.post("/api/stroke", json=brush(color="#ABCDEF")).get_json()
    assert state["strokes"][0]["color"] == "#abcdef"


def test_r2_invalid_color_is_rejected_with_a_message(client):
    """R2: An invalid color gets a 400 error and a helpful message."""
    res = client.post("/api/stroke", json=brush(color="purple-ish"))
    assert res.status_code == 400
    assert "hex color" in res.get_json()["error"]


# ---------- R3: brush ----------

def test_r3_drawing_a_stroke_adds_it(client):
    """R3: Sending a brush stroke adds it to the canvas."""
    state = client.post("/api/stroke", json=brush()).get_json()
    assert len(state["strokes"]) == 1
    assert state["strokes"][0]["tool"] == "brush"
    assert state["can_undo"] is True


def test_r3_bad_stroke_is_rejected_and_canvas_unchanged(client):
    """R3: A broken stroke is refused and nothing is drawn."""
    res = client.post("/api/stroke", json=brush(points=[]))
    assert res.status_code == 400
    assert client.get("/api/state").get_json()["strokes"] == []


def test_r3_missing_body_is_rejected(client):
    """R3: A request with no stroke data is refused safely."""
    res = client.post("/api/stroke", data="not json", content_type="text/plain")
    assert res.status_code == 400


# ---------- R4: eraser ----------

def test_r4_eraser_stroke_is_added(client):
    """R4: Erasing adds an eraser stroke over the drawing."""
    client.post("/api/stroke", json=brush())
    state = client.post("/api/stroke", json=eraser()).get_json()
    assert [s["tool"] for s in state["strokes"]] == ["brush", "eraser"]
    assert state["strokes"][1]["color"] is None


# ---------- R5: undo / redo ----------

def test_r5_undo_and_redo_through_the_app(client):
    """R5: The Undo and Redo buttons step back and forward."""
    client.post("/api/stroke", json=brush(color="#111111"))
    client.post("/api/stroke", json=brush(color="#222222"))

    state = client.post("/api/undo").get_json()
    assert [s["color"] for s in state["strokes"]] == ["#111111"]
    assert state["can_redo"] is True

    state = client.post("/api/redo").get_json()
    assert [s["color"] for s in state["strokes"]] == ["#111111", "#222222"]
    assert state["can_redo"] is False


def test_r5_undo_with_nothing_to_undo_is_safe(client):
    """R5: Pressing Undo on a blank canvas just returns the blank canvas."""
    res = client.post("/api/undo")
    assert res.status_code == 200
    assert res.get_json()["strokes"] == []


# ---------- R6: save and reopen ----------

def test_r6_save_and_reopen_through_the_app(client):
    """R6: Save artwork, start fresh, then reopen it with everything back."""
    client.post("/api/stroke", json=brush(color="#2a9d5c"))
    client.post("/api/item", json=item("heart"))
    res = client.post("/api/save", json={"name": "My House"})
    assert res.get_json() == {"saved": "My_House"}

    client.post("/api/clear")
    assert client.get("/api/saves").get_json() == ["My_House"]

    state = client.post("/api/load", json={"name": "My_House"}).get_json()
    assert state["strokes"][0]["color"] == "#2a9d5c"
    assert state["strokes"][1]["item"] == "heart"
    assert state["can_undo"] is False


def test_r6_saving_over_a_name_asks_first(client):
    """R6: Saving with a used name returns 409 until the user confirms."""
    client.post("/api/stroke", json=brush(color="#111111"))
    client.post("/api/save", json={"name": "art"})
    client.post("/api/stroke", json=brush(color="#222222"))

    res = client.post("/api/save", json={"name": "art"})
    assert res.status_code == 409
    assert res.get_json()["exists"] is True

    res = client.post("/api/save", json={"name": "art", "overwrite": True})
    assert res.status_code == 200
    state = client.post("/api/load", json={"name": "art"}).get_json()
    assert len(state["strokes"]) == 2


def test_r6_saving_without_a_name_is_rejected(client):
    """R6: Saving with a blank name gives a helpful 400 error."""
    res = client.post("/api/save", json={"name": "  "})
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_r6_opening_a_missing_artwork_gives_404(client):
    """R6: Opening a name that isn't saved gives a 404 error."""
    assert client.post("/api/load", json={"name": "nope"}).status_code == 404


def test_r6_opening_a_damaged_file_gives_400_and_keeps_current_work(client, save_dir):
    """R6: A damaged file can't be opened, and the current drawing is kept."""
    client.post("/api/stroke", json=brush())
    save_dir.mkdir(parents=True, exist_ok=True)
    (save_dir / "bad.json").write_text('{"strokes": "oops"}', encoding="utf-8")
    assert client.post("/api/load", json={"name": "bad"}).status_code == 400
    assert len(client.get("/api/state").get_json()["strokes"]) == 1
    assert (save_dir / "bad.json").exists()


def test_r6_tests_never_touch_the_real_saves_folder(client, save_dir):
    """R6: The app under test saves only to the temporary folder."""
    client.post("/api/save", json={"name": "temp-only"})
    assert (save_dir / "temp-only.json").exists()
    assert save_dir != storage.SAVE_DIR


# ---------- R7: shapes, letters and numbers ----------

def test_r7_page_shows_every_item_to_place(client):
    """R7: Every shape, letter and number has a button on the page."""
    html = client.get("/").get_data(as_text=True)
    for i in list_items():
        assert 'data-item="' + i["id"] + '"' in html
    assert 'id="item-size"' in html
    assert 'data-tool="place"' in html and 'data-tool="select"' in html


def test_r7_page_has_no_template_menu_any_more(client):
    """R7: The coloring template menu has been replaced."""
    html = client.get("/").get_data(as_text=True)
    assert 'id="template-select"' not in html
    assert "Coloring templates" not in html


def test_r7_choosing_a_template_is_no_longer_possible(client):
    """R7: The old 'choose a template' and 'list templates' requests are gone."""
    assert client.post("/api/template", json={"id": "fish"}).status_code == 404
    assert client.get("/api/templates").status_code == 404
    assert client.get("/api/state").get_json()["template"] is None


def test_r7_item_list_api_gives_shape_outlines(client):
    """R7: The browser can fetch every item, with outlines for the shapes."""
    items = client.get("/api/items").get_json()
    assert [i["id"] for i in items] == [i["id"] for i in list_items()]
    for i in items:
        if i["kind"] == "shape":
            assert len(i["points"]) >= 3
        else:
            assert "points" not in i


def test_r7_placing_an_item_through_the_app(client):
    """R7: Placing an item adds it, filled with the color, and selects it."""
    client.post("/api/stroke", json=brush())
    res = client.post("/api/item", json=item("A", color="#2F5BD3", size=150, x=100, y=50))
    assert res.status_code == 200
    data = res.get_json()
    assert data["selected"] == 1
    placed = data["strokes"][1]
    assert (placed["tool"], placed["item"], placed["color"], placed["size"]) == ("item", "A", "#2f5bd3", 150)
    assert (placed["x"], placed["y"]) == (100, 50)
    assert data["can_undo"] is True


def test_r7_placing_an_item_can_be_undone_through_the_app(client):
    """R7: Undo removes a placed item."""
    client.post("/api/item", json=item())
    assert client.post("/api/undo").get_json()["strokes"] == []


def test_r7_bad_item_is_rejected_and_canvas_unchanged(client):
    """R7: An unknown item gets a 400 error and nothing is placed."""
    res = client.post("/api/item", json=item("dragon"))
    assert res.status_code == 400
    assert "error" in res.get_json()
    assert client.get("/api/state").get_json()["strokes"] == []


def test_r7_recoloring_a_placed_item_through_the_app(client):
    """R7: Picking a color while an item is selected re-colors it."""
    index = client.post("/api/item", json=item(color="#e63946")).get_json()["selected"]
    res = client.post("/api/item/recolor", json={"index": index, "color": "#7fe0c3"})
    assert res.status_code == 200
    assert res.get_json()["strokes"][index]["color"] == "#7fe0c3"
    assert client.post("/api/undo").get_json()["strokes"][index]["color"] == "#e63946"


def test_r7_recoloring_a_brush_stroke_is_refused(client):
    """R7: Only items can be re-colored; brush strokes keep their color."""
    client.post("/api/stroke", json=brush(color="#111111"))
    res = client.post("/api/item/recolor", json={"index": 0, "color": "#7fe0c3"})
    assert res.status_code == 400
    assert client.get("/api/state").get_json()["strokes"][0]["color"] == "#111111"


def test_r7_clicking_finds_the_item_to_select(client):
    """R7: The Select tool asks which item is under the pointer."""
    client.post("/api/item", json=item(size=100, x=400, y=300))
    assert client.post("/api/item-at", json={"x": 420, "y": 310}).get_json() == {"index": 0}
    assert client.post("/api/item-at", json={"x": 10, "y": 10}).get_json() == {"index": None}
    assert client.post("/api/item-at", json={"x": "left", "y": 10}).status_code == 400


def test_r7_old_save_with_a_template_still_opens_with_its_outline(client, save_dir):
    """R7: Artwork saved with a template in an earlier round opens, and its outline can be drawn."""
    write_old_save(save_dir, "old_cat", "cat")
    state = client.post("/api/load", json={"name": "old_cat"}).get_json()
    assert state["template"] == "cat"
    assert state["strokes"][0]["color"] == "#2a9d5c"
    outline = client.get("/api/templates/cat")
    assert outline.status_code == 200
    assert len(outline.get_json()["shapes"]) > 0


def test_r7_opening_an_old_save_does_not_change_the_file(client, save_dir):
    """R7: Opening old artwork never rewrites its file."""
    path = write_old_save(save_dir, "old_fish", "fish")
    before = path.read_bytes()
    client.post("/api/load", json={"name": "old_fish"})
    assert path.read_bytes() == before


def test_r7_saving_old_artwork_again_keeps_its_template(client, save_dir):
    """R7: Adding to an old artwork and saving it keeps its template outline."""
    write_old_save(save_dir, "old_house", "house")
    client.post("/api/load", json={"name": "old_house"})
    client.post("/api/item", json=item("7"))
    client.post("/api/save", json={"name": "old_house", "overwrite": True})
    state = client.post("/api/load", json={"name": "old_house"}).get_json()
    assert state["template"] == "house"
    assert state["strokes"][1]["item"] == "7"


def test_r7_unknown_template_outline_gives_404(client):
    """R7: Asking for the outline of a template that doesn't exist gives 404."""
    assert client.get("/api/templates/nope").status_code == 404


# ---------- R8: clear canvas ----------

def test_r8_clear_wipes_the_canvas(client):
    """R8: The Clear button removes all strokes and placed items."""
    client.post("/api/stroke", json=brush())
    client.post("/api/item", json=item())
    state = client.post("/api/clear").get_json()
    assert state["strokes"] == []
    assert state["template"] is None


def test_r8_clear_removes_an_old_template_outline(client, save_dir):
    """R8: Clearing old artwork removes its template outline too."""
    write_old_save(save_dir, "old_star", "star")
    client.post("/api/load", json={"name": "old_star"})
    assert client.post("/api/clear").get_json()["template"] is None


def test_r8_clear_can_be_undone_through_the_app(client):
    """R8: Undo after Clear brings the artwork back."""
    client.post("/api/stroke", json=brush())
    client.post("/api/clear")
    state = client.post("/api/undo").get_json()
    assert len(state["strokes"]) == 1


def test_r8_clear_does_not_touch_saved_artwork(client, save_dir):
    """R8: Clearing the canvas never deletes saved files."""
    client.post("/api/stroke", json=brush())
    client.post("/api/save", json={"name": "safe"})
    client.post("/api/clear")
    assert (save_dir / "safe.json").exists()


# ---------- R9: recent colors ----------

def test_r9_page_has_a_recent_colors_area(client):
    """R9: The page has a place to show the recent colors."""
    html = client.get("/").get_data(as_text=True)
    assert 'id="recent-colors"' in html


def test_r9_recent_colors_start_empty_in_the_app(client):
    """R9: When the app starts, no colors have been picked yet."""
    assert client.get("/api/recent-colors").get_json() == []


def test_r9_picking_colors_updates_the_recent_list(client):
    """R9: Each picked color is added to the front of the list."""
    client.post("/api/recent-colors", json={"color": "#e63946"})
    res = client.post("/api/recent-colors", json={"color": "#2A9D5C"})
    assert res.status_code == 200
    assert res.get_json() == ["#2a9d5c", "#e63946"]
    assert client.get("/api/recent-colors").get_json() == ["#2a9d5c", "#e63946"]


def test_r9_app_shows_only_the_five_newest_colors_once_each(client):
    """R9: Through the app, the list holds 5 colors, newest first, no repeats."""
    for color in ["#111111", "#222222", "#333333", "#111111", "#444444", "#555555", "#666666"]:
        client.post("/api/recent-colors", json={"color": color})
    assert client.get("/api/recent-colors").get_json() == ["#666666", "#555555", "#444444", "#111111", "#333333"]


def test_r9_clicking_a_recent_color_selects_it_again(client):
    """R9: Clicking a recent color re-picks it (moves to front) and it can be painted with."""
    for color in ["#111111", "#222222", "#333333"]:
        client.post("/api/recent-colors", json={"color": color})
    recent = client.get("/api/recent-colors").get_json()
    clicked = recent[2]  # the oldest one, "#111111"
    assert client.post("/api/recent-colors", json={"color": clicked}).get_json()[0] == clicked
    state = client.post("/api/stroke", json=brush(color=clicked)).get_json()
    assert state["strokes"][0]["color"] == clicked


def test_r9_invalid_recent_color_is_rejected(client):
    """R9: An invalid color gets a 400 error and the list stays the same."""
    client.post("/api/recent-colors", json={"color": "#111111"})
    res = client.post("/api/recent-colors", json={"color": "not-a-color"})
    assert res.status_code == 400
    assert "hex color" in res.get_json()["error"]
    assert client.get("/api/recent-colors").get_json() == ["#111111"]


def test_r9_recent_colors_are_not_part_of_undo_or_clear(client):
    """R9: Undo and Clear change the drawing, not the recent colors."""
    client.post("/api/stroke", json=brush())
    client.post("/api/recent-colors", json={"color": "#111111"})
    client.post("/api/undo")
    client.post("/api/clear")
    assert client.get("/api/recent-colors").get_json() == ["#111111"]


def test_r9_recent_colors_are_not_written_to_disk(client, save_dir):
    """R9: Recent colors live only while the app runs; nothing is saved to disk."""
    client.post("/api/recent-colors", json={"color": "#111111"})
    assert not save_dir.exists()


# ---------- R10: rename saved artwork ----------

def test_r10_page_has_rename_controls(client):
    """R10: The page has a box for the new name and a Rename button."""
    html = client.get("/").get_data(as_text=True)
    assert 'id="rename-name"' in html
    assert 'id="rename-btn"' in html


def test_r10_rename_through_the_app_keeps_the_artwork(client):
    """R10: Rename a saved artwork, then reopen it under the new name."""
    client.post("/api/stroke", json=brush(color="#2a9d5c"))
    client.post("/api/item", json=item("circle"))
    client.post("/api/save", json={"name": "draft"})

    res = client.post("/api/rename", json={"old_name": "draft", "new_name": "My Cat"})
    assert res.status_code == 200
    assert res.get_json() == {"renamed": "My_Cat"}
    assert client.get("/api/saves").get_json() == ["My_Cat"]

    client.post("/api/clear")
    state = client.post("/api/load", json={"name": "My_Cat"}).get_json()
    assert state["strokes"][0]["color"] == "#2a9d5c"
    assert state["strokes"][1]["item"] == "circle"


def test_r10_rename_onto_a_used_name_asks_first(client):
    """R10: Renaming onto another artwork's name returns 409 until the user confirms."""
    client.post("/api/stroke", json=brush(color="#111111"))
    client.post("/api/save", json={"name": "mine"})
    client.post("/api/stroke", json=brush(color="#222222"))
    client.post("/api/save", json={"name": "taken"})

    res = client.post("/api/rename", json={"old_name": "mine", "new_name": "taken"})
    assert res.status_code == 409
    assert res.get_json()["exists"] is True
    assert client.get("/api/saves").get_json() == ["mine", "taken"]  # nothing changed

    res = client.post("/api/rename", json={"old_name": "mine", "new_name": "taken", "overwrite": True})
    assert res.status_code == 200
    assert client.get("/api/saves").get_json() == ["taken"]
    state = client.post("/api/load", json={"name": "taken"}).get_json()
    assert len(state["strokes"]) == 1  # it's "mine" (1 stroke), not the old "taken" (2)


def test_r10_overwrite_must_be_exactly_true(client):
    """R10: Only a real yes (overwrite: true) replaces another artwork."""
    client.post("/api/save", json={"name": "mine"})
    client.post("/api/save", json={"name": "taken"})
    res = client.post("/api/rename", json={"old_name": "mine", "new_name": "taken", "overwrite": "yes"})
    assert res.status_code == 409
    assert client.get("/api/saves").get_json() == ["mine", "taken"]


def test_r10_renaming_a_missing_artwork_gives_404(client):
    """R10: Renaming a name that isn't saved gives a 404 error."""
    res = client.post("/api/rename", json={"old_name": "ghost", "new_name": "boo"})
    assert res.status_code == 404
    assert "error" in res.get_json()


def test_r10_blank_new_name_gives_400_and_keeps_the_artwork(client):
    """R10: A blank new name gives a helpful 400 error and nothing is renamed."""
    client.post("/api/save", json={"name": "keep"})
    res = client.post("/api/rename", json={"old_name": "keep", "new_name": "   "})
    assert res.status_code == 400
    assert client.get("/api/saves").get_json() == ["keep"]


def test_r10_renaming_does_not_change_the_open_canvas(client):
    """R10: Renaming a saved file leaves the drawing on screen as it is."""
    client.post("/api/stroke", json=brush())
    client.post("/api/save", json={"name": "art"})
    client.post("/api/rename", json={"old_name": "art", "new_name": "art2"})
    state = client.get("/api/state").get_json()
    assert len(state["strokes"]) == 1
    assert state["can_undo"] is True


# ---------- R11: flip and rotate ----------

def test_r11_page_has_flip_and_rotate_buttons(client):
    """R11: The page has Flip left-right, Flip top-bottom and Rotate buttons."""
    html = client.get("/").get_data(as_text=True)
    assert 'id="flip-h-btn"' in html
    assert 'id="flip-v-btn"' in html
    assert 'id="rotate-btn"' in html


def test_r11_rotate_through_the_app_turns_90_degrees_per_click(client):
    """R11: Each Rotate click turns the selected item another 90 degrees."""
    index = client.post("/api/item", json=item()).get_json()["selected"]
    angles = [client.post("/api/item/rotate", json={"index": index}).get_json()["strokes"][index]["rotation"]
              for _ in range(4)]
    assert angles == [90, 180, 270, 0]


def test_r11_flip_through_the_app(client):
    """R11: The flip buttons mirror the selected item left-right or top-bottom."""
    index = client.post("/api/item", json=item("F")).get_json()["selected"]
    state = client.post("/api/item/flip", json={"index": index, "direction": "horizontal"}).get_json()
    assert state["strokes"][index]["flip_x"] is True
    state = client.post("/api/item/flip", json={"index": index, "direction": "vertical"}).get_json()
    assert state["strokes"][index]["flip_y"] is True


def test_r11_flip_and_rotate_can_be_undone_through_the_app(client):
    """R11: Undo steps back through flips and rotations one at a time."""
    index = client.post("/api/item", json=item()).get_json()["selected"]
    client.post("/api/item/rotate", json={"index": index})
    client.post("/api/item/flip", json={"index": index, "direction": "horizontal"})
    state = client.post("/api/undo").get_json()
    assert state["strokes"][index]["flip_x"] is False
    assert state["strokes"][index]["rotation"] == 90
    state = client.post("/api/undo").get_json()
    assert state["strokes"][index]["rotation"] == 0
    state = client.post("/api/redo").get_json()
    assert state["strokes"][index]["rotation"] == 90


def test_r11_flip_and_rotate_need_a_placed_item(client):
    """R11: Flipping or rotating a brush stroke or a missing item gives 400."""
    client.post("/api/stroke", json=brush())
    assert client.post("/api/item/rotate", json={"index": 0}).status_code == 400
    assert client.post("/api/item/rotate", json={}).status_code == 400
    assert client.post("/api/item/flip", json={"index": 3, "direction": "vertical"}).status_code == 400


def test_r11_unknown_flip_direction_gives_400(client):
    """R11: Only horizontal and vertical flips are allowed."""
    index = client.post("/api/item", json=item()).get_json()["selected"]
    res = client.post("/api/item/flip", json={"index": index, "direction": "sideways"})
    assert res.status_code == 400
    assert client.get("/api/state").get_json()["strokes"][index]["flip_x"] is False


def test_r11_flips_and_rotations_are_saved(client):
    """R11: A flipped and rotated item looks the same after saving and reopening."""
    index = client.post("/api/item", json=item("R")).get_json()["selected"]
    client.post("/api/item/rotate", json={"index": index})
    client.post("/api/item/flip", json={"index": index, "direction": "vertical"})
    client.post("/api/save", json={"name": "turned"})
    client.post("/api/clear")
    placed = client.post("/api/load", json={"name": "turned"}).get_json()["strokes"][0]
    assert (placed["rotation"], placed["flip_x"], placed["flip_y"]) == (270, False, True)


# ---------- R15: gallery of saved artwork ----------

def test_r15_gallery_api_lists_artworks_newest_first(client, save_dir):
    """R15: /api/gallery gives every saved artwork, the most recently saved first."""
    write_old_save(save_dir, "older", None)  # saved on 2026-10-01
    client.post("/api/stroke", json=brush())
    assert client.post("/api/save", json={"name": "today"}).status_code == 200
    names = [entry["name"] for entry in client.get("/api/gallery").get_json()]
    assert names == ["today", "older"]


def test_r15_gallery_api_gives_what_the_preview_draws(client):
    """R15: Each entry has the artwork's strokes and placed items, exactly as opening it would give."""
    client.post("/api/stroke", json=brush(color="#123456"))
    client.post("/api/item", json=item(name="heart"))
    client.post("/api/item/rotate", json={"index": 1})
    client.post("/api/save", json={"name": "mine"})
    [entry] = client.get("/api/gallery").get_json()
    opened = client.post("/api/load", json={"name": "mine"}).get_json()
    assert entry["name"] == "mine"
    assert entry["damaged"] is False
    assert entry["strokes"] == opened["strokes"]
    assert entry["template"] is None
    assert entry["strokes"][1]["rotation"] == 90


def test_r15_gallery_shows_old_saves_with_their_template(client, save_dir):
    """R15: Artwork saved before Round 3 appears with its template outline, so its preview looks the same."""
    write_old_save(save_dir, "old-flower", "flower")
    [entry] = client.get("/api/gallery").get_json()
    assert entry["template"] == "flower"
    assert entry["strokes"][0]["color"] == "#2a9d5c"


def test_r15_gallery_marks_damaged_files_without_breaking(client, save_dir):
    """R15: A damaged file is listed as damaged (nothing to draw); the others still come through."""
    client.post("/api/save", json={"name": "good"})
    (save_dir / "broken.json").write_text("{oops", encoding="utf-8")
    (save_dir / "bad-stroke.json").write_text(json.dumps({"saved_at": "2026-01-01T00:00:00", "strokes": [5]}),
                                              encoding="utf-8")
    entries = {e["name"]: e for e in client.get("/api/gallery").get_json()}
    assert entries["good"]["damaged"] is False
    for name in ("broken", "bad-stroke"):
        assert entries[name]["damaged"] is True
        assert entries[name]["strokes"] == []


def test_r15_gallery_is_empty_with_no_saves(client):
    """R15: With nothing saved, the gallery list is empty."""
    assert client.get("/api/gallery").get_json() == []


def test_r15_looking_at_the_gallery_changes_nothing(client, save_dir):
    """R15: Opening the gallery doesn't change the canvas, its undo history, or any save file."""
    client.post("/api/stroke", json=brush())
    client.post("/api/save", json={"name": "keep"})
    write_old_save(save_dir, "old", "flower")
    files_before = {p.name: p.read_bytes() for p in save_dir.iterdir()}
    state_before = client.get("/api/state").get_json()
    client.get("/api/gallery")
    assert client.get("/api/state").get_json() == state_before
    assert {p.name: p.read_bytes() for p in save_dir.iterdir()} == files_before


def test_r15_opening_from_the_gallery_uses_the_normal_open(client):
    """R15: A gallery entry's name opens the artwork through /api/load, like the Open button."""
    client.post("/api/stroke", json=brush(color="#654321"))
    client.post("/api/save", json={"name": "pick-me"})
    client.post("/api/clear")
    name = client.get("/api/gallery").get_json()[0]["name"]
    state = client.post("/api/load", json={"name": name}).get_json()
    assert state["strokes"][0]["color"] == "#654321"
