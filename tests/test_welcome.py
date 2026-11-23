"""Tests for the welcome message (R16: "Welcome to PixelSpace" at the top
center of the page, written in cursive).

The tests read what the app really serves: the page (/), the stylesheet
(/static/style.css) and app.js.
"""

import re

import pytest

from test_icon import declarations, split_media
from test_style import resolve, rgb, strip_comments

MESSAGE = "Welcome to PixelSpace"
ACCENT_PURPLE = "#7b4fd6"  # the user's choice: the app's accent purple


@pytest.fixture
def page(client):
    response = client.get("/")
    assert response.status_code == 200
    # Windows line endings (\r\n) are turned into \n, so the checks below work with either.
    return response.get_data(as_text=True).replace("\r\n", "\n")


@pytest.fixture
def css(client):
    return client.get("/static/style.css").get_data(as_text=True).replace("\r\n", "\n")


def welcome_rules(css):
    """The declarations for .welcome outside any @media block (comments removed)."""
    outside, _ = split_media(css)
    return declarations(outside, ".welcome")


def body_html(page):
    return page.split("<body>", 1)[1]


def without_comments(html):
    return re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)


def font_names(font_family):
    """'"Segoe Script", cursive' -> ['segoe script', 'cursive']"""
    return [name.strip().strip("\"'").lower() for name in font_family.split(",")]


# ---------- what the message says ----------

def test_r16_page_shows_the_welcome_message(page):
    """R16: The page has an element with exactly the words "Welcome to PixelSpace"."""
    match = re.search(r'<(\w+) class="welcome">\s*([^<]*?)\s*</\1>', page)
    assert match, "no element with class 'welcome' found"
    assert match.group(2) == MESSAGE


def test_r16_message_appears_only_once(page):
    """R16: There is one welcome message, not several."""
    assert without_comments(page).count(MESSAGE) == 1


# ---------- where it is: the top center of the page ----------

def test_r16_message_is_the_first_thing_on_the_page(page):
    """R16: The message is the first element in the page body, so it is at the very top."""
    first_tag = re.search(r"<(\w+)[^>]*>", without_comments(body_html(page)))
    assert first_tag.group(0) == '<p class="welcome">'


def test_r16_message_is_above_the_top_bar(page):
    """R16 (the user's answer): The message has its own line above the top bar, not inside it."""
    body = without_comments(body_html(page))
    assert body.index(MESSAGE) < body.index('<header class="topbar">')
    top_bar = body.split('<header class="topbar">', 1)[1].split("</header>", 1)[0]
    assert MESSAGE not in top_bar


def test_r16_top_bar_logo_and_buttons_stay(page):
    """R16 (the user's answer): The logo and the Undo, Redo and Clear buttons are still in the top bar."""
    top_bar = page.split('<header class="topbar">', 1)[1].split("</header>", 1)[0]
    assert 'class="logo"' in top_bar
    for button_id in ("undo-btn", "redo-btn", "clear-btn"):
        assert f'id="{button_id}"' in top_bar


def test_r16_message_is_centered(css):
    """R16: The text is centered."""
    assert welcome_rules(css).get("text-align") == "center"


def test_r16_message_spans_the_whole_width(page, css):
    """R16: It is a normal block across the full page width, so its center is the page's center."""
    rules = welcome_rules(css)
    assert rules.get("position", "static") == "static"
    for name in ("width", "max-width", "float", "display"):
        assert name not in rules, f".welcome should not set {name}"
    # A <p> straight inside <body> is a block as wide as the page.
    assert re.search(r"<body>\s*(<!--.*?-->\s*)*<p class=\"welcome\">", page, flags=re.DOTALL)


# ---------- how it looks: cursive, accent purple ----------

def test_r16_message_is_written_in_cursive(css):
    """R16: The font list ends with the browser's own 'cursive' font, so it is always cursive."""
    names = font_names(welcome_rules(css).get("font-family", ""))
    assert names[-1] == "cursive"


def test_r16_cursive_fonts_are_tried_in_the_chosen_order(css):
    """R16: Segoe Script first, then Brush Script MT, then the browser's cursive font."""
    names = font_names(welcome_rules(css).get("font-family", ""))
    assert names == ["segoe script", "brush script mt", "cursive"]


def test_r16_no_font_is_downloaded(page, css):
    """R16 (the user's answer): Only fonts already on the computer; nothing is fetched from outside."""
    assert "@font-face" not in strip_comments(css)
    assert "@import" not in strip_comments(css)
    assert not re.search(r"url\(\s*['\"]?(https?:)?//", strip_comments(css))
    for href in re.findall(r'<link[^>]+href="([^"]+)"', page):
        assert not re.match(r"(https?:)?//", href), f"page loads something from outside: {href}"


def test_r16_message_is_accent_purple(css):
    """R16 (the user's answer): The message is the app's accent purple, #7b4fd6."""
    color = resolve(css, welcome_rules(css).get("color", ""))
    assert rgb(color) == rgb(ACCENT_PURPLE)


def test_r16_message_sits_on_the_gradient(css):
    """R16: The message has no box of its own, so the pastel gradient (R12) shows behind it."""
    rules = welcome_rules(css)
    for name in ("background", "background-color"):
        assert rules.get(name, "transparent") == "transparent"


def test_r16_message_is_shown_on_every_screen_size(css):
    """R16: No @media block hides the message or changes its font."""
    _, blocks = split_media(css)
    for condition, inside in blocks.items():
        rules = declarations(inside, ".welcome")
        assert rules.get("display") != "none", f"hidden by @media {condition}"
        assert rules.get("visibility") != "hidden", f"hidden by @media {condition}"
        assert "font-family" not in rules, f"font changed by @media {condition}"


# ---------- it is only decoration, never part of the artwork ----------

def test_r16_message_is_outside_the_canvas_and_the_gallery(page):
    """R16: The message is not inside the canvas box or the gallery pop-up, so it never covers them."""
    canvas_box = page.split('id="canvas-wrap"', 1)[1].split("</div>", 1)[0]
    assert MESSAGE not in canvas_box
    gallery = page.split('id="gallery"', 1)[1].split('id="toast"', 1)[0]
    assert MESSAGE not in gallery
    assert page.index(MESSAGE) < page.index("<main")


def test_r16_message_is_never_drawn_by_app_js(client):
    """R16: app.js draws the canvas, the PNG download and the gallery previews; it never mentions the message."""
    script = client.get("/static/app.js").get_data(as_text=True).lower()
    assert "welcome" not in script


def test_r16_message_is_not_part_of_saved_artwork(client, save_dir):
    """R16: Saving stores only the drawing, not the welcome message."""
    assert client.post("/api/save", json={"name": "plain"}).status_code == 200
    saved_text = (save_dir / "plain.json").read_text(encoding="utf-8").lower()
    assert "welcome" not in saved_text
    assert "cursive" not in saved_text
