"""Tests for storage.py (R6: saving and reopening artwork, R10: renaming it).

All of these use a temporary folder, never the real saves/ folder.
"""

import json

import pytest

import storage
from storage import (
    ArtworkExistsError,
    artwork_exists,
    clean_name,
    list_artworks,
    load_artwork,
    rename_artwork,
    save_artwork,
)

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


# ---------- R10: renaming saved artwork ----------

OTHER_ARTWORK = {
    "template": None,
    "strokes": [{"tool": "brush", "color": "#2a9d5c", "size": 4, "points": [[5.0, 5.0]]}],
}


def test_r10_rename_keeps_the_artwork(save_dir):
    """R10: After renaming, the artwork opens under the new name with everything kept."""
    save_artwork(ARTWORK, "old name", save_dir)
    new = rename_artwork("old_name", "New Name", save_dir)
    assert new == "New_Name"
    data = load_artwork("New_Name", save_dir)
    assert data["strokes"] == ARTWORK["strokes"]
    assert data["template"] == "flower"


def test_r10_old_name_is_gone_and_new_name_is_listed(save_dir):
    """R10: The saved list shows the new name instead of the old one."""
    save_artwork(ARTWORK, "before", save_dir)
    rename_artwork("before", "after", save_dir)
    assert list_artworks(save_dir) == ["after"]


def test_r10_name_inside_the_file_is_updated(save_dir):
    """R10: The name stored inside the saved file matches its new name."""
    save_artwork(ARTWORK, "before", save_dir)
    rename_artwork("before", "after", save_dir)
    assert load_artwork("after", save_dir)["name"] == "after"
    assert not list(save_dir.glob("*.tmp"))  # no leftover temp files


def test_r10_rename_to_a_used_name_asks_first(save_dir):
    """R10: Renaming onto another artwork's name is refused until the user confirms."""
    save_artwork(ARTWORK, "mine", save_dir)
    save_artwork(OTHER_ARTWORK, "taken", save_dir)
    with pytest.raises(ArtworkExistsError):
        rename_artwork("mine", "taken", save_dir)
    # Nothing changed: both artworks are still there, untouched.
    assert list_artworks(save_dir) == ["mine", "taken"]
    assert load_artwork("mine", save_dir)["strokes"] == ARTWORK["strokes"]
    assert load_artwork("taken", save_dir)["strokes"] == OTHER_ARTWORK["strokes"]


def test_r10_rename_replaces_the_other_artwork_when_user_confirms(save_dir):
    """R10: With overwrite=True (the user said yes), the renamed artwork takes the name."""
    save_artwork(ARTWORK, "mine", save_dir)
    save_artwork(OTHER_ARTWORK, "taken", save_dir)
    assert rename_artwork("mine", "taken", save_dir, overwrite=True) == "taken"
    assert list_artworks(save_dir) == ["taken"]
    assert load_artwork("taken", save_dir)["strokes"] == ARTWORK["strokes"]


def test_r10_rename_to_the_same_name_changes_nothing(save_dir):
    """R10: Renaming to the same name is not a clash and keeps the artwork."""
    save_artwork(ARTWORK, "same", save_dir)
    assert rename_artwork("same", "same", save_dir) == "same"
    assert list_artworks(save_dir) == ["same"]
    assert load_artwork("same", save_dir)["strokes"] == ARTWORK["strokes"]


def test_r10_changing_only_upper_lower_case_works(save_dir):
    """R10: 'cat' -> 'Cat' isn't treated as clashing with itself (matters on Windows)."""
    save_artwork(ARTWORK, "cat", save_dir)
    assert rename_artwork("cat", "Cat", save_dir) == "Cat"
    assert list_artworks(save_dir) == ["Cat"]
    assert load_artwork("Cat", save_dir)["strokes"] == ARTWORK["strokes"]


def test_r10_renaming_a_missing_artwork_gives_a_clear_error(save_dir):
    """R10: Renaming something that isn't saved raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        rename_artwork("ghost", "anything", save_dir)


@pytest.mark.parametrize("bad_name", ["", "   ", "???", None])
def test_r10_unusable_new_name_is_rejected_and_artwork_kept(save_dir, bad_name):
    """R10: A new name with no letters or numbers is refused; the artwork is untouched."""
    save_artwork(ARTWORK, "keep", save_dir)
    with pytest.raises(ValueError):
        rename_artwork("keep", bad_name, save_dir)
    assert list_artworks(save_dir) == ["keep"]


def test_r10_new_name_is_cleaned_and_stays_in_the_folder(save_dir):
    """R10: A tricky new name like '../escape' still ends up inside saves/."""
    save_artwork(ARTWORK, "start", save_dir)
    assert rename_artwork("start", "../escape", save_dir) == "escape"
    assert (save_dir / "escape.json").exists()
    assert not (save_dir.parent / "escape.json").exists()


def test_r10_damaged_file_can_still_be_renamed_without_changing_it(save_dir):
    """R10: Renaming a damaged file moves it but never changes its contents."""
    save_dir.mkdir(parents=True)
    (save_dir / "broken.json").write_text("{ not json", encoding="utf-8")
    rename_artwork("broken", "still_broken", save_dir)
    assert (save_dir / "still_broken.json").read_text(encoding="utf-8") == "{ not json"
    assert list_artworks(save_dir) == ["still_broken"]
