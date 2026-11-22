"""End-to-end tests of the web app using Flask's test client.

These act like the browser: they send the same requests the page sends.
They save into a temporary folder, never the real saves/ folder.
"""

import storage
from colors import PALETTE
from conftest import brush, eraser


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
    client.post("/api/template", json={"id": "house"})
    res = client.post("/api/save", json={"name": "My House"})
    assert res.get_json() == {"saved": "My_House"}

    client.post("/api/clear")
    assert client.get("/api/saves").get_json() == ["My_House"]

    state = client.post("/api/load", json={"name": "My_House"}).get_json()
    assert state["strokes"][0]["color"] == "#2a9d5c"
    assert state["template"] == "house"
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


# ---------- R7: coloring templates ----------

def test_r7_template_menu_is_on_the_page(client):
    """R7: The page lists the coloring templates to pick from."""
    html = client.get("/").get_data(as_text=True)
    for t in client.get("/api/templates").get_json():
        assert f'value="{t["id"]}"' in html


def test_r7_template_details_can_be_fetched(client):
    """R7: The browser can fetch a template's shapes to draw it."""
    data = client.get("/api/templates/cat").get_json()
    assert data["id"] == "cat"
    assert len(data["shapes"]) > 0


def test_r7_unknown_template_gives_404(client):
    """R7: Asking for a template that doesn't exist gives 404."""
    assert client.get("/api/templates/nope").status_code == 404
    assert client.post("/api/template", json={"id": "nope"}).status_code == 404


def test_r7_choose_and_remove_a_template(client):
    """R7: Users can pick a template, then go back to no template."""
    assert client.post("/api/template", json={"id": "fish"}).get_json()["template"] == "fish"
    assert client.post("/api/template", json={"id": None}).get_json()["template"] is None


# ---------- R8: clear canvas ----------

def test_r8_clear_wipes_the_canvas(client):
    """R8: The Clear button removes all strokes and the template."""
    client.post("/api/stroke", json=brush())
    client.post("/api/template", json={"id": "star"})
    state = client.post("/api/clear").get_json()
    assert state["strokes"] == []
    assert state["template"] is None


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
