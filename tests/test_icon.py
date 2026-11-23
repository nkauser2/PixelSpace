"""Tests for the deer icon (R13: on the canvas and in the browser tab;
R14: half size on narrow screens).

The tests read what the app really serves: the page (/), the stylesheet
(/static/style.css) and the deer picture (/static/deer.svg).
"""

import re
import xml.etree.ElementTree as ET

import pytest

from test_style import rgb, strip_comments

SVG = "{http://www.w3.org/2000/svg}"


# ---------- small helpers ----------

def split_media(css):
    """Split the CSS into (rules outside any @media block, {condition: CSS inside it}).

    For example "a{x:1} @media (max-width: 9px) { a{x:2} }" gives
    ("a{x:1} ", {"(max-width: 9px)": " a{x:2} "}).
    """
    css = strip_comments(css)
    outside, blocks = "", {}
    position = 0
    for match in re.finditer(r"@media([^{]+)\{", css):
        if match.start() < position:
            continue  # inside a block we already read
        outside += css[position:match.start()]
        depth, end = 1, match.end()
        while depth:
            depth += {"{": 1, "}": -1}.get(css[end], 0)
            end += 1
        blocks[match.group(1).strip()] = css[match.end():end - 1]
        position = end
    return outside + css[position:], blocks


def declarations(css, selector):
    """The declarations of the rules for exactly `selector`; later rules win."""
    found = {}
    for selectors, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        if selector in [s.strip() for s in selectors.split(",")]:
            for part in body.split(";"):
                if ":" in part:
                    name, value = part.split(":", 1)
                    found[name.strip()] = value.strip()
    return found


def pixels(value):
    match = re.fullmatch(r"(\d+(?:\.\d+)?)px", value.strip())
    assert match, f"expected a size in px, got {value!r}"
    return float(match.group(1))


@pytest.fixture
def page(client):
    response = client.get("/")
    assert response.status_code == 200
    return response.get_data(as_text=True)


@pytest.fixture
def css(client):
    return client.get("/static/style.css").get_data(as_text=True)


@pytest.fixture
def deer(client):
    """The deer picture, read as XML."""
    response = client.get("/static/deer.svg")
    assert response.status_code == 200
    return ET.fromstring(response.get_data())


def tab_icon_href(page):
    match = re.search(r'<link rel="icon"[^>]*href="([^"]+)"', page)
    assert match, "the page has no <link rel=\"icon\">"
    return match.group(1)


def canvas_icon_tag(page):
    match = re.search(r'<img[^>]*class="deer-icon"[^>]*>', page)
    assert match, "the page has no <img class=\"deer-icon\">"
    return match.group(0)


def group_color(deer, group_id, attribute):
    group = deer.find(f".//{SVG}g[@id='{group_id}']")
    assert group is not None, f"deer.svg has no group with id {group_id!r}"
    return group.get(attribute)


# ---------- R13 ----------

def test_r13_deer_is_the_browser_tab_icon(page, client):
    """R13: The page names the deer as its tab icon (favicon), and the file is served as SVG."""
    href = tab_icon_href(page)
    assert href.endswith("/deer.svg")
    assert re.search(r'<link rel="icon" type="image/svg\+xml"', page)
    response = client.get(href)
    assert response.status_code == 200
    assert response.mimetype == "image/svg+xml"


def test_r13_canvas_icon_and_tab_icon_are_the_same_picture(page):
    """R13: The deer on the canvas comes from the same file as the tab icon."""
    src = re.search(r'src="([^"]+)"', canvas_icon_tag(page)).group(1)
    assert src == tab_icon_href(page)


def test_r13_deer_sits_on_top_of_the_canvas(page):
    """R13: The deer is inside the canvas box, after (so above) all the canvas layers."""
    wrap = re.search(r'<div class="canvas-wrap".*?</div>', page, flags=re.DOTALL).group(0)
    assert 'class="deer-icon"' in wrap
    assert wrap.index('class="deer-icon"') > wrap.rindex("<canvas")


def test_r13_deer_is_in_the_top_right_corner_of_the_canvas(css):
    """R13: The deer is pinned to the top and right edges of the canvas box."""
    outside, _ = split_media(css)
    icon = declarations(outside, ".deer-icon")
    assert icon.get("position") == "absolute"
    assert "top" in icon and "right" in icon
    assert "left" not in icon and "bottom" not in icon
    # The canvas box is what the deer is positioned against.
    assert declarations(outside, ".canvas-wrap").get("position") == "relative"


def test_r13_drawing_works_underneath_the_deer(css):
    """R13: Clicks and touches go through the deer to the canvas, so it never blocks drawing."""
    outside, _ = split_media(css)
    assert declarations(outside, ".deer-icon").get("pointer-events") == "none"


def test_r13_deer_body_is_dark_purple(deer):
    """R13: The deer's head and ears are dark purple."""
    red, green, blue = rgb(group_color(deer, "deer-body", "fill"))
    assert blue > red > green, "purple: lots of blue, some red, little green"
    assert max(red, green, blue) < 0xA0, "dark"


def test_r13_deer_antlers_are_pink(deer):
    """R13: The antlers are pink."""
    red, green, blue = rgb(group_color(deer, "antlers", "stroke"))
    assert red > blue > green, "pink: mostly red, then blue, little green"
    assert red > 0xD0, "bright, not dark red"
    assert group_color(deer, "antlers", "fill") == "none"


def test_r13_only_the_antlers_are_pink(deer):
    """R13: Apart from the antlers, the deer uses no pink, so it reads as a purple deer."""
    antlers = deer.find(f".//{SVG}g[@id='antlers']")
    antler_parts = set(antlers.iter())
    for element in deer.iter():
        if element in antler_parts:
            continue
        for attribute in ("fill", "stroke"):
            color = element.get(attribute, "")
            if re.fullmatch(r"#[0-9a-fA-F]{6}", color):
                red, green, blue = rgb(color)
                is_white = min(red, green, blue) > 0xF0
                assert is_white or not (red > blue > green and red > 0xD0), f"{color} looks pink"


def test_r13_deer_has_a_see_through_background(deer):
    """R13: Nothing fills the picture's background, so only the deer covers the canvas."""
    assert deer.find(f".//{SVG}rect") is None
    assert deer.get("style") is None and deer.get("fill") is None
    assert deer.get("viewBox") == "0 0 64 64"


def test_r13_deer_is_not_part_of_saved_artwork(client, save_dir):
    """R13: The deer is not saved with the artwork."""
    assert client.post("/api/save", json={"name": "plain"}).status_code == 200
    saved_text = (save_dir / "plain.json").read_text(encoding="utf-8").lower()
    assert "deer" not in saved_text
    assert "icon" not in saved_text


def test_r13_deer_is_not_in_the_downloaded_png(client):
    """R13: The PNG download only copies the canvas layers; app.js never draws the deer."""
    script = client.get("/static/app.js").get_data(as_text=True).lower()
    assert "deer" not in script
    assert "icon" not in script


# ---------- R14 ----------

def narrow_screen_rules(css):
    """The CSS inside the @media block for windows under 600px wide, and its width limit."""
    _, blocks = split_media(css)
    for condition, inside in blocks.items():
        match = re.fullmatch(r"\(max-width:\s*(\d+(?:\.\d+)?)px\)", condition)
        if match and ".deer-icon" in inside:
            return inside, float(match.group(1))
    raise AssertionError("no @media (max-width: ...) block resizes the deer")


def test_r14_deer_is_64px_at_full_size(css):
    """R14: Outside the narrow-screen rule, the deer is 64 x 64 pixels."""
    outside, _ = split_media(css)
    icon = declarations(outside, ".deer-icon")
    assert pixels(icon["width"]) == 64
    assert pixels(icon["height"]) == 64


def test_r14_deer_is_half_size_on_narrow_screens(css):
    """R14: On narrow screens, the deer's width and height are half of the full size."""
    outside, _ = split_media(css)
    full = declarations(outside, ".deer-icon")
    inside, _ = narrow_screen_rules(css)
    narrow = declarations(inside, ".deer-icon")
    assert pixels(narrow["width"]) == pixels(full["width"]) / 2 == 32
    assert pixels(narrow["height"]) == pixels(full["height"]) / 2 == 32


def test_r14_narrow_means_a_window_under_600px_wide(css):
    """R14: 599px (and anything in between, like 599.5px when zoomed) is narrow; 600px is not."""
    _, limit = narrow_screen_rules(css)
    assert 599.9 <= limit < 600


def test_r14_gap_to_the_canvas_edges_is_halved_too(css):
    """R14: The half-size deer keeps the same look in the corner: its gap to the edges is halved."""
    outside, _ = split_media(css)
    full = declarations(outside, ".deer-icon")
    inside, _ = narrow_screen_rules(css)
    narrow = declarations(inside, ".deer-icon")
    assert pixels(narrow["top"]) == pixels(full["top"]) / 2
    assert pixels(narrow["right"]) == pixels(full["right"]) / 2


def test_r14_only_the_size_changes_on_narrow_screens(css):
    """R14: The narrow-screen rule only resizes the deer; it stays in the corner and lets clicks through."""
    inside, _ = narrow_screen_rules(css)
    assert set(declarations(inside, ".deer-icon")) <= {"width", "height", "top", "right"}


def test_r14_tab_icon_is_the_same_file_on_every_screen(page):
    """R14: Only the deer on the page changes size; the tab icon is still the one deer.svg."""
    assert len(re.findall(r'<link rel="icon"', page)) == 1
    assert tab_icon_href(page).endswith("/deer.svg")
