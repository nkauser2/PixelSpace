"""Tests for storage.py (R6: saving and reopening artwork).

All of these use a temporary folder, never the real saves/ folder.
"""

import json

import pytest

import storage
from storage import ArtworkExistsError, artwork_exists, clean_name, list_artworks, load_artwork, save_artwork

ARTWORK = {
    "template": "flower",
    "strokes": [{"tool": "brush", "color": "#e63946", "size": 8, "points": [[1.0, 2.0], [3.0, 4.0]]}],
}


def test_r6_save_then_load_gives_back_the_same_artwork(save_dir):
    """R6: Saved artwork reopens exactly as it was."""
    name = save_artwork(ARTWORK, "My Flower", save_dir)
    data = load_artwork(name, save_dir)
    assert data["strokes"] == ARTWORK["strokes"]
    assert data["template"] == "flower"
    assert data["app"] == "PixelSpace"


def test_r6_save_creates_the_folder_and_a_json_file(save_dir):
    """R6: Saving creates saves/ if needed and writes a readable JSON file."""
    assert not save_dir.exists()
    save_artwork(ARTWORK, "first", save_dir)
    path = save_dir / "first.json"
    assert path.exists()
    assert json.loads(path.read_text(encoding="utf-8"))["name"] == "first"
    assert not list(save_dir.glob("*.tmp"))  # no leftover temp files


def test_r6_saved_artworks_are_listed_alphabetically(save_dir):
    """R6: The 'open' list shows every saved artwork, sorted by name."""
    for name in ["zebra", "apple", "Mango"]:
        save_artwork(ARTWORK, name, save_dir)
    assert list_artworks(save_dir) == sorted(["zebra", "apple", "Mango"])


def test_r6_list_is_empty_before_anything_is_saved(save_dir):
    """R6: With no saves yet, the list is simply empty."""
    assert list_artworks(save_dir) == []


def test_r6_existing_artwork_is_not_replaced_without_permission(save_dir):
    """R6: Saving over an existing name is refused unless the user confirms."""
    save_artwork(ARTWORK, "keep-me", save_dir)
    with pytest.raises(ArtworkExistsError):
        save_artwork({"template": None, "strokes": []}, "keep-me", save_dir)
    assert load_artwork("keep-me", save_dir)["strokes"] == ARTWORK["strokes"]


def test_r6_existing_artwork_is_replaced_when_user_confirms(save_dir):
    """R6: With overwrite=True (the user said yes), the save is replaced."""
    save_artwork(ARTWORK, "update-me", save_dir)
    save_artwork({"template": None, "strokes": []}, "update-me", save_dir, overwrite=True)
    assert load_artwork("update-me", save_dir)["strokes"] == []
    assert list_artworks(save_dir) == ["update-me"]


def test_r6_artwork_exists_check(save_dir):
    """R6: The app can check whether a name is already used."""
    assert not artwork_exists("thing", save_dir)
    save_artwork(ARTWORK, "thing", save_dir)
    assert artwork_exists("thing", save_dir)


@pytest.mark.parametrize("given, expected", [
    ("My Flower", "My_Flower"),
    ("  spaced   out  ", "spaced_out"),
    ("../../secret", "secret"),
    ("C:\\Windows\\evil", "CWindowsevil"),
    ("cat?*<>|.json", "catjson"),
    ("a" * 80, "a" * storage.MAX_NAME_LENGTH),
])
def test_r6_names_are_cleaned_into_safe_file_names(given, expected):
    """R6: Names become safe file names that can't escape the saves folder."""
    assert clean_name(given) == expected


@pytest.mark.parametrize("bad_name", ["", "   ", "???", None, 123])
def test_r6_empty_or_unusable_names_are_rejected(bad_name):
    """R6: A name with no letters or numbers is refused with a clear message."""
    with pytest.raises(ValueError):
        clean_name(bad_name)


def test_r6_tricky_names_still_save_inside_the_folder(save_dir):
    """R6: Even a name like '../escape' is saved inside saves/."""
    save_artwork(ARTWORK, "../escape", save_dir)
    assert (save_dir / "escape.json").exists()
    assert not (save_dir.parent / "escape.json").exists()


def test_r6_loading_a_missing_artwork_gives_a_clear_error(save_dir):
    """R6: Opening a name that doesn't exist raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_artwork("ghost", save_dir)


def test_r6_damaged_file_is_reported_and_left_alone(save_dir):
    """R6: A broken save file gives an error and is NOT deleted or changed."""
    save_dir.mkdir(parents=True)
    broken = save_dir / "broken.json"
    broken.write_text("{ this is not json", encoding="utf-8")
    with pytest.raises(ValueError, match="damaged"):
        load_artwork("broken", save_dir)
    assert broken.read_text(encoding="utf-8") == "{ this is not json"


def test_r6_storage_has_no_delete_function():
    """R6: Saved artwork can never be deleted by the app (project rule)."""
    names = [n.lower() for n in dir(storage)]
    assert not any("delete" in n or "remove" in n for n in names)
