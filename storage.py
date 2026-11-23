"""Saving, reopening (R6) and renaming (R10) artwork.

Each artwork is saved as a JSON file inside the saves/ folder.
Safety rules (from CLAUDE.md):
  * There is NO delete function - saved artwork is never removed.
  * An existing save is only replaced when the user confirms (overwrite=True).
    This applies to saving AND to renaming onto a name that's already used.
  * Damaged files are reported, never deleted or changed.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

SAVE_DIR = Path(__file__).parent / "saves"
MAX_NAME_LENGTH = 50


class ArtworkExistsError(Exception):
    """Raised when saving would replace an artwork the user hasn't agreed to replace."""


def clean_name(name):
    """Turn a user-typed name into a safe file name.

    Keeps letters, numbers, spaces, dashes and underscores; spaces become "_".
    This also stops tricks like "../secret" from escaping the saves folder.
    """
    if not isinstance(name, str):
        raise ValueError("Please type a name for your artwork.")
    name = re.sub(r"[^A-Za-z0-9 _-]", "", name).strip()
    name = re.sub(r"\s+", "_", name)[:MAX_NAME_LENGTH]
    if not name:
        raise ValueError("Please use letters or numbers in your artwork's name.")
    return name


def _path_for(name, save_dir):
    return Path(save_dir) / f"{clean_name(name)}.json"


def artwork_exists(name, save_dir=SAVE_DIR):
    return _path_for(name, save_dir).exists()


def save_artwork(artwork, name, save_dir=SAVE_DIR, overwrite=False):
    """Save `artwork` (a dict from Canvas.to_dict()) under `name`.

    Returns the cleaned name it was saved as. Raises ArtworkExistsError if the
    name is taken and overwrite is False.
    """
    save_dir = Path(save_dir)
    path = _path_for(name, save_dir)
    if path.exists() and not overwrite:
        raise ArtworkExistsError(f"An artwork called '{path.stem}' already exists.")

    save_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "app": "PixelSpace",
        "version": 1,
        "name": path.stem,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "template": artwork.get("template"),
        "strokes": artwork.get("strokes", []),
    }

    _write_json_safely(path, data)
    return path.stem


def _write_json_safely(path, data):
    """Write to a temporary file first, then swap it in. If something goes
    wrong mid-write, the file that was there before is left untouched."""
    temp_path = path.with_suffix(".json.tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(temp_path, path)


def rename_artwork(old_name, new_name, save_dir=SAVE_DIR, overwrite=False):
    """Give a saved artwork a new name (R10). Returns the cleaned new name.

    The artwork's file is moved, not copied, so its strokes and template are
    never lost along the way. Raises:
      * ValueError if the new name has no letters or numbers,
      * FileNotFoundError if there's no artwork called `old_name`,
      * ArtworkExistsError if a DIFFERENT artwork already uses the new name
        and overwrite is False (the user hasn't agreed to replace it).
    """
    old_path = _path_for(old_name, save_dir)
    new_path = _path_for(new_name, save_dir)
    if not old_path.exists():
        raise FileNotFoundError(f"No saved artwork called '{old_path.stem}'.")
    if old_path.name == new_path.name:
        return new_path.stem  # same name: nothing to do

    # On Windows, "cat.json" and "Cat.json" are the same file, so renaming
    # "cat" to "Cat" must not count as clashing with another artwork.
    clashes = new_path.exists() and not os.path.samefile(old_path, new_path)
    if clashes and not overwrite:
        raise ArtworkExistsError(f"An artwork called '{new_path.stem}' already exists.")

    os.replace(old_path, new_path)  # move the file to its new name in one step
    _update_name_inside(new_path)
    return new_path.stem


def _update_name_inside(path):
    """Store the new name inside the file too. A damaged file is left exactly
    as it is - its name on disk has changed, which is all that's needed."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return
    if isinstance(data, dict):
        data["name"] = path.stem
        _write_json_safely(path, data)


def list_artworks(save_dir=SAVE_DIR):
    """Names of all saved artworks, in alphabetical order."""
    save_dir = Path(save_dir)
    if not save_dir.exists():
        return []
    return sorted(p.stem for p in save_dir.glob("*.json"))


def gallery_artworks(save_dir=SAVE_DIR):
    """Every saved artwork for the gallery (R15), the most recently saved first.

    Each entry is {"name", "saved_at", "artwork"}, where "artwork" is the
    file's data, or None if the file is damaged. Files are only read, never
    changed. The order uses the "saved_at" time written when the artwork was
    last saved, so renaming (which doesn't save) keeps an artwork's place.
    Artworks saved in the same second go in name order. Files with no usable
    save time (such as damaged ones) go last.
    """
    save_dir = Path(save_dir)
    if not save_dir.exists():
        return []
    entries = []
    for name in list_artworks(save_dir):  # alphabetical, so equal times stay in name order
        try:
            artwork = load_artwork(name, save_dir)
        except ValueError:
            artwork = None
        saved_at = artwork.get("saved_at") if artwork else None
        entries.append({"name": name, "saved_at": saved_at if _is_save_time(saved_at) else None, "artwork": artwork})
    # Newest first. Python's sort keeps the name order for equal times, and
    # "" (no time) sorts after every real time.
    entries.sort(key=lambda entry: entry["saved_at"] or "", reverse=True)
    return entries


def _is_save_time(value):
    """True for a time like "2026-11-21T21:19:33", the way save_artwork writes it."""
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return False
    return True


def load_artwork(name, save_dir=SAVE_DIR):
    """Read a saved artwork and return its data as a dict.

    Raises FileNotFoundError if it doesn't exist, or ValueError if the file is
    damaged (the file itself is left alone).
    """
    path = _path_for(name, save_dir)
    if not path.exists():
        raise FileNotFoundError(f"No saved artwork called '{path.stem}'.")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ValueError(f"The file for '{path.stem}' is damaged and can't be opened.")
    if not isinstance(data, dict):
        raise ValueError(f"The file for '{path.stem}' is damaged and can't be opened.")
    return data
