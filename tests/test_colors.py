"""Tests for colors.py (R2: palette and custom colors)."""

import pytest

from colors import DEFAULT_COLOR, PALETTE, is_valid_hex, normalize_hex


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
