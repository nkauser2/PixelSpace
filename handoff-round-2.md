# Handoff: PixelSpace, end of Round 2

Written for a fresh session starting the next round. Standing rules for every session are in `CLAUDE.md`, so read that first. This file only covers what is true at the end of Round 2.

## Current state

- **Every requirement R1–R10 is implemented and tested.** R1–R8 were done in Round 1. R9 and R10 were done in Round 2.
  - **R9:** the 5 most recently picked colors, each shown once; clicking one selects it again.
  - **R10:** rename a saved artwork without losing it, and confirm before replacing one that already has the new name.
- **Tests:** `python -m pytest` gives **190 passed** (checked on Python 3.12.10 and Flask 3.1.3).
- **Git:** branch `master`, working tree clean apart from this file and the CLAUDE.md edits. The last commit is `7e15eb4`. Nothing has been pushed.
- **Round 2 commits**, oldest first:
  - `95cccc6`: spec.md updated for Round 2
  - `74cd911`: R9 logic and tests
  - `8e5c681`: R9 API and page
  - `0efbbdb`: R10 storage and tests
  - `99efdbd`: R10 API and page
  - `7976e89`: decision records
  - `1b9c647`: README
  - `668543a`: decision records renamed to four digits
  - `7e15eb4`: numbering rule added to CLAUDE.md
- **No handoff file existed from Round 1**, and there was no `docs/decisions/` folder before Round 2.

### Where things are

| File | What it holds |
|---|---|
| `app.py` | Flask server. `create_app(save_dir=None)` builds the app, and the JSON API lives under `/api/...` |
| `canvas_model.py` | `Canvas`: strokes, template, undo/redo, clear (R1, R3–R5, R7, R8) |
| `colors.py` | Palette and hex checks (R2); `RecentColors` and `MAX_RECENT_COLORS = 5` (R9) |
| `storage.py` | Save, list, load (R6); `rename_artwork` (R10). Files go in `saves/*.json` |
| `coloring_templates.py` | The 5 coloring templates (R7) |
| `templates/index.html`, `static/app.js`, `static/style.css` | The browser page |
| `tests/` | One file per module, plus `test_requirements_coverage.py` |
| `docs/decisions/` | 0001–0003 (Round 2), written as Y-statements |
| `spec.md` | The original spec plus a "Round 2" section with exact R9 and R10 behavior |

### API added in Round 2

- `GET /api/recent-colors` returns the list, newest first.
- `POST /api/recent-colors {"color": "#hex"}` returns the updated list. A bad color gives 400.
- `POST /api/rename {"old_name", "new_name", "overwrite"}` responds with:
  - 200 `{"renamed": name}` on success
  - 409 `{"exists": true}` if another artwork already has the new name
  - 404 if the old name isn't saved
  - 400 if the new name is unusable

## How to run

```
pip install -r requirements.txt
python app.py
```
Then open http://127.0.0.1:5000.

## How to run the tests

```
python -m pytest
```
The tests use a temporary folder (`tmp_path`) through the `save_dir` and `client` fixtures in `tests/conftest.py`. They never touch the real `saves/` folder.

## Decisions made in Round 2, and why

### The user's answers to my questions (asked before any code was written)

1. **What counts as picking a color:** a palette click, a recent-color click, or closing the custom picker (its `change` event). Dragging inside the picker (`input`) only updates the current color, so in-between shades don't fill the list.
2. **Re-picking moves a color to the front.** The list is always newest first.
3. **Recent colors last only while the app runs.** They survive reloading the page but not restarting `python app.py`, and they are never written to disk.
4. **Renaming onto a used name replaces that artwork after the user confirms.** No backup is kept.

### Recorded in docs/decisions/

- **0001: recent colors are kept in the server's memory** (`app.config["RECENT_COLORS"]`), not only in the browser. This lets pytest test the R9 rules and keeps the list across page reloads.
- **0002: rename moves the file with a single `os.replace`**, not copy-then-delete. A rename either fully happens or doesn't happen, and `storage.py` still has no delete function.
- **0003: picking a color is not part of undo/redo**, Clear doesn't empty the list, and recent colors are not saved with artwork. Undo only steps through drawing actions, and the save file format is unchanged.

### Smaller choices the user didn't ask for

- The recent list starts empty.
- `#ABC` and `#aabbcc` count as one color.
- A case-only rename (e.g. `cat` → `Cat`) is not a clash. `os.path.samefile` handles this on Windows.
- Renaming to the same name does nothing and shows no error.
- A damaged save file can still be renamed, and its contents are left untouched.
- The `name` field inside the JSON file is updated when an artwork is renamed.
- The Rename box acts on the artwork chosen in the "Saved artwork" list. If that is the open artwork, the save-name box updates too.
- Renaming doesn't change the canvas on screen or its undo history.
- The rename confirm message warns that the other artwork's drawing will be lost.
- The atomic write step in `storage.py` is now a shared helper, `_write_json_safely`, used by both save and rename.

## Unresolved

- **R9 and R10 were tried by hand in a browser (recent colors, rename, and the name-already-taken confirm) and it worked** Node isn't installed, so `static/app.js` wasn't even syntax-checked, and the pytest tests only check the server and the HTML. Before building on it, run `python app.py` and try picking colors, the custom picker, and renaming (including a clash).
- **Commit `7976e89`'s message still says "001-003".** The files were renamed later in `668543a`. Rewriting old messages would mean amending, which is not allowed.
- **No Round 1 handoff exists**, so Round 1's reasoning is only recorded in the commit messages and code comments.

## Warnings for the next session

- **Raise `LAST_REQUIREMENT` when you add requirements.** It is in `tests/test_requirements_coverage.py`, currently 10. That test fails if any test name doesn't start with `test_r<N>_` for a known requirement, or if a requirement has no tests. Raise it in the same commit as the new tests, or the suite goes red.
- **Never use "delete" or "remove" in a name in `storage.py`.** `test_r6_storage_has_no_delete_function` fails if any name in the module contains "delete" or "remove", including imported names like `from os import remove`. Use `os.replace` or `Path.replace`.
- **The real `saves/` folder exists on this computer and holds the user's artwork.** It is git-ignored. Never delete, move or change anything in it, and only use temporary folders in tests.
- **The app keeps one canvas and one recent-colors list in memory** (`app.config`). It is built for one local user, not many at once.
- **Windows file names ignore upper/lower case.** Keep that in mind for anything that compares or creates save file names.
- **Git warns "LF will be replaced by CRLF" on commits.** This is harmless and expected on this machine.
- **CLAUDE.md says "the next one is 0004".** Update that line whenever a new decision record is added.
- **How this user works:**
  - They want unclear requirements listed and asked about before any code is written.
  - They want small commits whose messages say what changed and why.
  - They have often asked to see a commit message and give an OK before committing.
  - They want a list of every decision they didn't ask for at the end of a round.
  - They write the handoff request separately and read and edit files before committing them.
