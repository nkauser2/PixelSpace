"""Tests for the gallery page parts (R15: a button opens a pop-up with a small
preview of every saved artwork, five per row, newest first).

The /api/gallery tests are in test_app.py and test_storage.py. These tests read
what the app really serves: the page (/), the stylesheet and app.js.
"""

import re

import pytest

from test_icon import declarations, split_media
from test_style import background_of, is_white, strip_comments


@pytest.fixture
def page(client):
    response = client.get("/")
    assert response.status_code == 200
    return response.get_data(as_text=True)


@pytest.fixture
def css(client):
    return client.get("/static/style.css").get_data(as_text=True)


@pytest.fixture
def script(client):
    # Windows line endings (\r\n) are turned into \n, so the checks below work with either.
    return client.get("/static/app.js").get_data(as_text=True).replace("\r\n", "\n")


def rules(css, selector):
    """The declarations for exactly `selector` in the whole stylesheet (comments removed)."""
    return declarations(strip_comments(css), selector)


def gallery_html(page):
    """The HTML of the gallery pop-up (from its opening tag to the toast after it)."""
    match = re.search(r'<div id="gallery".*?(?=<div id="toast")', page, flags=re.DOTALL)
    assert match, "the page has no gallery pop-up"
    return match.group(0)


def function_body(script, name):
    """The text of a function in app.js, from its name to the next top-level line."""
    match = re.search(rf"function {name}\(.*?\n}}\n", script, flags=re.DOTALL)
    assert match, f"app.js has no function {name}"
    return match.group(0)


# ---------- the button and the pop-up ----------

def test_r15_page_has_a_gallery_button_in_my_artwork(page):
    """R15: The gallery is opened with a button in the "My artwork" section."""
    my_artwork = page[page.index("<h2>My artwork</h2>"):page.index("</aside>")]
    assert 'id="gallery-btn"' in my_artwork
    assert "Gallery" in my_artwork


def test_r15_gallery_is_a_hidden_pop_up_until_the_button_is_clicked(page):
    """R15: The pop-up is on the page but hidden at first, so it never covers the canvas until asked for."""
    tag = re.search(r'<div id="gallery"[^>]*>', page).group(0)
    assert "hidden" in tag
    assert 'role="dialog"' in gallery_html(page)


def test_r15_gallery_pop_up_sits_over_the_whole_page(page, css):
    """R15: The pop-up is outside the page layout and fixed over the window (the user chose a pop-up)."""
    layout = page[page.index('<main class="layout">'):page.index("</main>")]
    assert 'id="gallery"' not in layout
    backdrop = rules(css, ".gallery-backdrop")
    assert backdrop["position"] == "fixed"
    assert backdrop["inset"] == "0"
    # Without this, display:flex would show the pop-up even while it is hidden.
    assert rules(css, ".gallery-backdrop[hidden]")["display"] == "none"


def test_r15_gallery_has_a_close_button_grid_and_empty_message(page):
    """R15: The pop-up can be closed, has a grid for the previews, and a message for when nothing is saved."""
    html = gallery_html(page)
    assert 'id="gallery-close"' in html
    assert 'id="gallery-grid"' in html
    empty = re.search(r'<p id="gallery-empty"[^>]*>(.*?)</p>', html, flags=re.DOTALL)
    assert empty and "hidden" in empty.group(0)
    assert "No saved artwork" in empty.group(1)


def test_r15_toasts_show_above_the_gallery(css):
    """R15: Messages (like "Couldn't open that artwork") are not hidden behind the pop-up."""
    assert int(rules(css, ".toast")["z-index"]) > int(rules(css, ".gallery-backdrop")["z-index"])


# ---------- five per row, on every screen ----------

def test_r15_gallery_shows_five_artworks_per_row(css):
    """R15: The preview grid always has exactly five equal columns."""
    outside, _ = split_media(css)
    grid = declarations(outside, ".gallery-grid")
    assert grid["display"] == "grid"
    assert re.fullmatch(r"repeat\(5,\s*minmax\(0,\s*1fr\)\)", grid["grid-template-columns"])


def test_r15_five_per_row_on_narrow_screens_too(css):
    """R15: No screen-size rule changes the gallery, so narrow screens (like 599px) also get five per row."""
    _, blocks = split_media(css)
    for condition, inside in blocks.items():
        assert ".gallery" not in inside, f"@media {condition} changes the gallery"


def test_r15_previews_have_a_white_background_like_the_canvas(css):
    """R15: A preview looks like the artwork: drawn on white, like the canvas and the PNG download."""
    assert is_white(background_of(css, ".gallery-preview"))


# ---------- the script ----------

def test_r15_gallery_button_loads_the_saved_artwork_list(script):
    """R15: Clicking the button fetches /api/gallery and shows the pop-up."""
    assert re.search(r'galleryBtn\.addEventListener\("click", openGallery\)', script)
    body = function_body(script, "openGallery")
    assert '"/api/gallery"' in body
    assert "gallery.hidden = false" in body


def test_r15_previews_keep_the_servers_newest_first_order(script):
    """R15: The previews are added in the order the server sends them (newest first), never re-sorted."""
    body = function_body(script, "openGallery")
    assert "for (const entry of res.data)" in body
    assert ".sort(" not in body


def test_r15_previews_are_drawn_with_the_same_code_as_the_canvas(script):
    """R15: A preview uses drawStroke and the template outline code, so it looks the same as the opened artwork."""
    body = function_body(script, "drawPreview")
    assert "drawStroke(ctx, stroke)" in body
    assert "drawTemplate(ctx," in body
    assert "ctx.scale(" in body  # shrunk to fit the small preview


def test_r15_clicking_a_preview_opens_it_like_the_open_button(script):
    """R15: A preview and the Open button use the same openArtwork, which asks before replacing a drawing."""
    open_artwork = function_body(script, "openArtwork")
    assert "confirm(" in open_artwork
    assert '"/api/load"' in open_artwork
    assert "openArtwork(name)" in function_body(script, "openFromGallery")
    assert "closeGallery()" in function_body(script, "openFromGallery")
    open_button = script[script.index("openBtn.addEventListener"):]
    assert "openArtwork(" in open_button[:open_button.index("});")]


def test_r15_damaged_artwork_cannot_be_opened_from_the_gallery(script):
    """R15: A damaged file is shown with a note instead of a preview, and its card can't be clicked."""
    body = function_body(script, "makeGalleryCard")
    assert "entry.damaged" in body
    assert "card.disabled = true" in body
    assert "Can't be shown" in body


def test_r15_escape_closes_the_gallery(script):
    """R15: The Escape key closes the pop-up, and drawing shortcuts don't act on the hidden canvas meanwhile."""
    keys = script[script.index('document.addEventListener("keydown"'):]
    assert re.search(r'if \(!gallery\.hidden\) \{\s*if \(event\.key === "Escape"\) closeGallery\(\);\s*return;', keys)


# ---------- page decorations are never in a preview ----------

def test_r15_gallery_has_no_page_decorations(page, script):
    """R15: The pop-up has no images (no deer), and previews are drawn only from the saved strokes."""
    html = gallery_html(page)
    assert "<img" not in html
    assert "deer" not in html.lower()
    body = function_body(script, "drawPreview").lower()
    for word in ("gradient", "deer", "drawimage"):
        assert word not in body


def test_r15_gallery_data_has_no_page_decorations(client):
    """R15: What the gallery receives is just the artwork, with nothing about the background or the deer."""
    client.post("/api/save", json={"name": "plain"})
    text = client.get("/api/gallery").get_data(as_text=True).lower()
    for word in ("deer", "icon", "background", "gradient"):
        assert word not in text
