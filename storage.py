"""Saving and reopening artwork (R6).

Each artwork is saved as a JSON file inside the saves/ folder.
Safety rules (from CLAUDE.md):
  * There is NO delete function - saved artwork is never removed.
  * An existing save is only replaced when the user confirms (overwrite=True).
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

    # Write to a temporary file first, then swap it in. If something goes
    # wrong mid-write, the user's previous save is left untouched.
    temp_path = path.with_suffix(".json.tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(temp_path, path)
    return path.stem


def list_artworks(save_dir=SAVE_DIR):
    """Names of all saved artworks, in alphabetical order."""
    save_dir = Path(save_dir)
    if not save_dir.exists():
        return []
    return sorted(p.stem for p in save_dir.glob("*.json"))


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
