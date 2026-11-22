"""Tests for colors.py (R2: palette and custom colors, R9: recent colors)."""

import pytest

from colors import DEFAULT_COLOR, MAX_RECENT_COLORS, PALETTE, RecentColors, is_valid_hex, normalize_hex


def test_r2_palette_has_plenty_of_colors():
    """R2: The built-in palette offers a good range of colors."""
    assert len(PALETTE) >= 12


def test_r2_every_palette_color_is_valid():
    """R2: Each palette color is a proper hex code with a friendly name."""
    for color in PALETTE:
        assert is_valid_hex(color["hex"]), color
        assert color["name"].strip(), color


def test_r2_palette_colors_and_names_are_unique():
    """R2: No color or name appears twice in the palette."""
    hexes = [c["hex"].lower() for c in PALETTE]
    names = [c["name"] for c in PALETTE]
    assert len(set(hexes)) == len(hexes)
    assert len(set(names)) == len(names)


def test_r2_default_color_is_in_the_palette():
    """R2: The app starts with a color that's in the palette."""
    assert DEFAULT_COLOR in [c["hex"] for c in PALETTE]


@pytest.mark.parametrize("color", ["#a1b2c3", "#ABC", "#000000", "#FFFFFF", "#fFfFfF"])
def test_r2_valid_custom_colors_are_accepted(color):
    """R2: Custom hex colors in short or long form are accepted."""
    assert is_valid_hex(color)


@pytest.mark.parametrize("color", ["red", "#12345g", "", "#1234", "123456", "#1234567", None, 255, "# abcdef"])
def test_r2_invalid_custom_colors_are_rejected(color):
    """R2: Anything that isn't a hex color is refused."""
    assert not is_valid_hex(color)


@pytest.mark.parametrize("given, expected", [("#ABC", "#aabbcc"), ("#A1B2C3", "#a1b2c3"), ("#123456", "#123456")])
def test_r2_colors_are_normalized(given, expected):
    """R2: Colors are stored in one standard form (7 characters, lowercase)."""
    assert normalize_hex(given) == expected


def test_r2_normalizing_an_invalid_color_gives_a_friendly_error():
    """R2: An invalid color raises a clear error message."""
    with pytest.raises(ValueError, match="not a valid hex color"):
        normalize_hex("blue")


# ---------- R9: recent colors ----------

def test_r9_recent_colors_start_empty():
    """R9: Before any color is picked, the recent list is empty."""
    assert RecentColors().colors == []


def test_r9_recent_colors_keep_at_most_five():
    """R9: Only the 5 most recently picked colors are kept."""
    assert MAX_RECENT_COLORS == 5
    recent = RecentColors()
    for color in ["#111111", "#222222", "#333333", "#444444", "#555555", "#666666"]:
        recent.pick(color)
    assert recent.colors == ["#666666", "#555555", "#444444", "#333333", "#222222"]


def test_r9_newest_color_is_first():
    """R9: The list is ordered newest first."""
    recent = RecentColors()
    recent.pick("#111111")
    recent.pick("#222222")
    assert recent.colors == ["#222222", "#111111"]


def test_r9_each_color_is_shown_only_once():
    """R9: Picking a color twice doesn't make it appear twice."""
    recent = RecentColors()
    recent.pick("#111111")
    recent.pick("#111111")
    assert recent.colors == ["#111111"]


def test_r9_picking_a_listed_color_again_moves_it_to_the_front():
    """R9: Re-picking a color (e.g. by clicking it in the list) makes it the newest."""
    recent = RecentColors()
    for color in ["#111111", "#222222", "#333333"]:
        recent.pick(color)
    recent.pick("#111111")
    assert recent.colors == ["#111111", "#333333", "#222222"]


def test_r9_repicking_does_not_push_another_color_out():
    """R9: Re-picking a listed color when the list is full keeps all 5 colors."""
    recent = RecentColors()
    for color in ["#111111", "#222222", "#333333", "#444444", "#555555"]:
        recent.pick(color)
    recent.pick("#111111")
    assert sorted(recent.colors) == ["#111111", "#222222", "#333333", "#444444", "#555555"]


def test_r9_same_color_in_different_forms_counts_once():
    """R9: "#ABC" and "#aabbcc" are the same color, so it's listed once."""
    recent = RecentColors()
    recent.pick("#ABC")
    recent.pick("#aabbcc")
    assert recent.colors == ["#aabbcc"]


def test_r9_pick_returns_the_clean_color():
    """R9: pick() gives back the color in its standard form."""
    assert RecentColors().pick("#FF00AA") == "#ff00aa"


@pytest.mark.parametrize("bad", ["red", "", None, 42, "#12345g"])
def test_r9_invalid_colors_are_refused_and_list_unchanged(bad):
    """R9: An invalid color raises an error and doesn't change the list."""
    recent = RecentColors()
    recent.pick("#111111")
    with pytest.raises(ValueError):
        recent.pick(bad)
    assert recent.colors == ["#111111"]


def test_r9_colors_list_cannot_be_changed_from_outside():
    """R9: Changing the returned list doesn't change the real recent list."""
    recent = RecentColors()
    recent.pick("#111111")
    recent.colors.append("#999999")
    assert recent.colors == ["#111111"]
