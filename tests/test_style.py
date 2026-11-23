"""Tests for how the page looks (R12: the pastel gradient background).

The tests read the stylesheet that the app really serves (/static/style.css)
and check the rules that make up the background.
"""

import re

import pytest

# The four gradient colors, in the order they must appear (R12).
GRADIENT_ORDER = ["lavender", "pink", "blue", "mint"]


# ---------- small helpers for reading the CSS ----------

def strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


def rule(css, selector):
    """The declarations of the rule for exactly `selector`, as a dict.

    For example rule(css, "body") -> {"margin": "0", "background": "...", ...}.
    If the selector has several rules, later ones win (just like in a browser).
    """
    declarations = {}
    for selectors, body in re.findall(r"([^{}]+)\{([^{}]*)\}", strip_comments(css)):
        if selector in [s.strip() for s in selectors.split(",")]:
            for part in body.split(";"):
                if ":" in part:
                    name, value = part.split(":", 1)
                    declarations[name.strip()] = value.strip()
    return declarations


def variables(css):
    """Every CSS variable defined in :root, e.g. {"--panel": "#ffffff"}."""
    return {name: value for name, value in rule(css, ":root").items() if name.startswith("--")}


def resolve(css, value):
    """Replace var(--name) with the variable's value, also inside other variables."""
    found = variables(css)
    for _ in range(10):  # variables can use other variables, so repeat a few times
        value = re.sub(r"var\((--[\w-]+)\)", lambda m: found.get(m.group(1), m.group(0)), value)
    return " ".join(value.split())  # tidy line breaks and extra spaces


def background_of(css, selector):
    declarations = rule(css, selector)
    return resolve(css, declarations.get("background", declarations.get("background-color", "")))


def rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def is_white(value):
    return value.strip().lower() in {"#fff", "#ffffff", "white"}


@pytest.fixture
def css(client):
    response = client.get("/static/style.css")
    assert response.status_code == 200
    return response.get_data(as_text=True)


@pytest.fixture
def gradient_colors(css):
    """The four gradient colors from the stylesheet, by name."""
    found = variables(css)
    return {name: found[f"--bg-{name}"] for name in GRADIENT_ORDER}


# ---------- R12 ----------

def test_r12_page_background_is_a_diagonal_gradient_in_the_right_order(css, gradient_colors):
    """R12: The page goes lavender -> soft pink -> baby blue -> mint green, top-left to bottom-right."""
    background = background_of(css, "body")
    assert background.startswith("linear-gradient(")
    assert "to bottom right" in background
    positions = [background.find(gradient_colors[name]) for name in GRADIENT_ORDER]
    assert -1 not in positions, "every gradient color must be used"
    assert positions == sorted(positions), "colors must appear in the order lavender, pink, blue, mint"


def test_r12_gradient_colors_are_light_pastels(gradient_colors):
    """R12: Each color is light (pastel) but still a real color, not white or grey."""
    for name, color in gradient_colors.items():
        red, green, blue = rgb(color)
        assert min(red, green, blue) >= 200, f"{name} {color} is too dark for a pastel"
        assert max(red, green, blue) - min(red, green, blue) >= 15, f"{name} {color} is too close to white/grey"


def test_r12_each_gradient_color_matches_its_name(gradient_colors):
    """R12: lavender is purple-ish, soft pink is pink, baby blue is blue, mint is green."""
    r, g, b = rgb(gradient_colors["lavender"])
    assert b > g and r > g, "lavender mixes red and blue"
    r, g, b = rgb(gradient_colors["pink"])
    assert r > b > g, "soft pink is mostly red, with some blue"
    r, g, b = rgb(gradient_colors["blue"])
    assert b > g > r, "baby blue is mostly blue"
    r, g, b = rgb(gradient_colors["mint"])
    assert g > b > r, "mint green is mostly green, with some blue"


def test_r12_gradient_covers_the_whole_window(css):
    """R12: The gradient fills the whole window, even on short or long pages."""
    body = rule(css, "body")
    assert body.get("margin") == "0", "no white edge around the page"
    assert body.get("min-height") == "100vh", "fills the window even when the page is short"
    assert body.get("background-attachment") == "fixed", "still fills the window when the page scrolls"


def test_r12_white_page_background_is_replaced(css):
    """R12: Neither the page nor the html element has a plain white (or plain) background any more."""
    for selector in ("html", "body"):
        background = background_of(css, selector)
        assert not is_white(background)
    assert "linear-gradient" in background_of(css, "body")


def test_r12_top_bar_shows_the_gradient(css):
    """R12: The top bar is see-through, so the gradient covers it too."""
    assert background_of(css, ".topbar") == "transparent"


def test_r12_top_bar_buttons_stay_white_and_readable(css):
    """R12: Undo, Redo and Clear keep their white background on top of the gradient."""
    assert is_white(background_of(css, ".btn"))


def test_r12_canvas_stays_white(css):
    """R12: The canvas is not covered by the gradient."""
    assert is_white(background_of(css, ".canvas-wrap"))


def test_r12_left_card_around_the_palette_stays_white(css):
    """R12: The whole left card (tools, colors, shapes, my artwork) stays white."""
    assert is_white(background_of(css, ".panel"))


def test_r12_palette_is_inside_the_white_card(client):
    """R12: The color palette sits inside the white left card, not on the gradient."""
    html = client.get("/").get_data(as_text=True)
    panel_start = html.index('<aside class="panel">')
    panel_end = html.index("</aside>")
    assert panel_start < html.index('id="palette"') < panel_end
    assert panel_start < html.index('id="recent-colors"') < panel_end


def test_r12_gradient_is_not_part_of_saved_artwork(client, save_dir):
    """R12: The background is only page styling; a save file holds just the drawing, as before."""
    assert client.post("/api/save", json={"name": "plain"}).status_code == 200
    saved_text = (save_dir / "plain.json").read_text(encoding="utf-8").lower()
    assert "gradient" not in saved_text
    assert "background" not in saved_text
