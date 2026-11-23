# Handoff: PixelSpace, end of Round 3

Written for a fresh session starting the next round. Standing rules for every session are in `CLAUDE.md`, so read that first. This file only covers what is true at the end of Round 3. The Round 2 handoff (`handoff-round-2.md`) still describes R9 and R10 accurately.

## Current state

- **Every requirement R1–R11 is implemented and tested.** In Round 3:
  - **R7 (changed):** the coloring templates were replaced by 44 items students place on the canvas: 8 shapes (circle, square, triangle, star, heart, diamond, hexagon, arrow), capital letters A–Z and digits 0–9. A placed item is filled with the current color, and the selected item can be re-colored.
  - **R11 (new):** Flip ↔, Flip ↕ and Rotate 90° (clockwise) buttons act on the selected item.
- **Tests:** `python -m pytest` gives **320 passed** (Python 3.12.10, Flask 3.1.3). `LAST_REQUIREMENT` is 11.
- **Git:** branch `master`. The last commit is `807a1da`. Nothing has been pushed. Uncommitted: this file and a CLAUDE.md edit, both waiting for the user to read them.
- **Round 3 commits**, oldest first:
  - `c66f96b`: spec.md Round 3 section
  - `7362c34`: `shapes.py` item catalogue and tests
  - `90ed9bd`: canvas model and API for items, flip and rotate, plus tests. **At this commit, 3 page tests fail.** They pass from the next commit; the commit message says so.
  - `da7ec56`: the page (item grid, Place/Select tools, flip/rotate buttons)
  - `601119c`: `coloring_templates.py` trimmed to old-save use only
  - `c89a6dd`: decision records 0004 and 0005, and the next-number line in CLAUDE.md
  - `807a1da`: README

### Where things are

| File | What it holds |
|---|---|
| `app.py` | Flask server. `create_app(save_dir=None)` builds the app, and the JSON API lives under `/api/...` |
| `canvas_model.py` | `Canvas`: strokes and placed items, undo/redo, clear (R1, R3–R5, R7, R8, R11); `make_item`, `item_point_on_canvas` |
| `shapes.py` | The 44 placeable items and the shape outlines (R7) |
| `coloring_templates.py` | Template outlines, **only** so artwork saved in Rounds 1–2 still shows them |
| `colors.py` | Palette and hex checks (R2); `RecentColors` (R9) |
| `storage.py` | Save, list, load (R6); rename (R10). Files go in `saves/*.json`. Unchanged in Round 3 |
| `templates/index.html`, `static/app.js`, `static/style.css` | The browser page |
| `tests/` | One file per module (`test_shapes.py` is new), plus `test_requirements_coverage.py` |
| `docs/decisions/` | 0001–0003 (Round 2) and 0004–0005 (Round 3), written as Y-statements |
| `spec.md` | Original spec plus "Round 2" and "Round 3" sections |

### How a placed item is stored

Items are entries in the same `strokes` list as brush and eraser strokes. They're drawn in list order:

```
{"tool": "item", "item": "star", "color": "#e63946", "size": 120,
 "x": 400.0, "y": 300.0, "rotation": 90, "flip_x": false, "flip_y": false}
```

- `x`, `y` are the item's center, and `size` is the width of its square box (20–400).
- `rotation` is 0/90/180/270, clockwise.
- An item's id is a shape name (`"star"`) or the character itself (`"A"`, `"7"`).
- Shape outlines are points in a 1 × 1 box centered on (0, 0).
- Letters and numbers are drawn by the browser as bold text.

### API changes in Round 3

- Added:
  - `GET /api/items` lists every item, and shapes also carry `points`.
  - `POST /api/item {"item", "color", "size", "x", "y"}` returns the state plus `"selected": index`.
  - `POST /api/item/recolor {"index", "color"}`.
  - `POST /api/item/rotate {"index"}`.
  - `POST /api/item/flip {"index", "direction": "horizontal" | "vertical"}`.
  - `POST /api/item-at {"x", "y"}` returns `{"index": n or null}` (the top item whose box contains the point).
  - A bad item, index, color, direction or position gives 400.
- Removed: `GET /api/templates` and `POST /api/template`. Both now return 404.
- Kept: `GET /api/templates/<id>`, so old saves can draw their outline.

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
The tests use a temporary folder through the `save_dir` and `client` fixtures in `tests/conftest.py`.

## Decisions made in Round 3, and why

### The user's answers to my questions (asked before any code was written)

1. **Coloring:** items are solid shapes filled with the current color. Picking a color while an item is selected re-colors it.
2. **Which items:** 8 shapes, A–Z (capitals only) and 0–9.
3. **What flip/rotate act on:** the selected item. A newly placed item is selected automatically, and the Select tool selects any item.
4. **Old saves with a template:** they still open and still show the template outline. No new template can be chosen.

### Recorded in docs/decisions/

- **0004: placed items share the ordered `strokes` list** with brush and eraser strokes. The rejected options were a separate items list or fixed stamps. As a result, the brush paints over items, the eraser erases them, and undo, clear and save needed no new code. Old save files keep the same format.
- **0005: flips are as seen on screen**, even after rotating. A flip toggles `flip_x`/`flip_y` and sets `rotation = 360 - rotation`. The browser must draw with the same steps as `item_point_on_canvas`.

### Written in spec.md (Round 3 section)

- Items are placed centered on the click. Their size and position can't change after placing.
- The Item size slider runs 20–400 and starts at 120.
- The selected item has a dashed box. Brush, eraser, undo, redo, clear and open all clear the selection.
- Rotate is clockwise. The three buttons are disabled when nothing is selected.
- Items are undoable, cleared by Clear, and saved with the artwork.

### Smaller choices not written in spec.md or a decision record

The user was asked whether to add these to spec.md and **hasn't answered yet**:

- P and S keyboard shortcuts for Place and Select.
- Shapes are drawn as filled outlines. Letters and numbers use bold system-font text, centered with `measureText`.
- The heart, circle and arrow outlines are my own designs. The buttons show symbols (● ■ ▲ ★ ♥ ◆ ⬢ ➜).
- Select uses each item's square box, not its exact outline.
- **Picking a color now switches to the brush only when the eraser is in use.** In Rounds 1–2 it always switched to the brush. This changes earlier behavior.
- Dragging inside the custom picker doesn't re-color the selected item. It's re-colored only when the picker closes.
- Re-coloring with the color an item already has adds no undo step.
- Items must be placed on the canvas (0–800, 0–600). Lowercase letters are refused.
- `list_templates` and its three menu tests were removed.
- Clear also removes an old save's template outline, and undo brings it back. This is unchanged from before.

## Unresolved

- **The spec.md question above has no answer yet.** The user may want the smaller choices added to the Round 3 section, and possibly a decision record (0006) for the color/brush change.
- **Commit `90ed9bd` is red on its own** (3 page tests). It can't be fixed without amending, which isn't allowed.
- **The page was checked only in headless Edge, through a scripted test page**: placing, selecting, flip, rotate, re-color, undo and the size slider all worked with no page errors. Nobody has tried it by hand yet. Freehand brush drawing wasn't part of that scripted check (it was unchanged this round).
- **Letters and numbers are drawn with the system font.** On a different computer, they may look slightly different or sit a little off-center in their box.

## Warnings for the next session

- **Not everything in `strokes` is a stroke.** Code that reads the list must check `tool` first: items have no `points`, and strokes have no `x`, `y` or `rotation`. `Canvas.from_dict` sends `"tool": "item"` entries to `make_item`.
- **Items are identified by their position in the list.** Anything that inserts into or reorders `strokes` would break the browser's `selectedIndex`. Today the list only grows at the end, or is replaced by undo, redo, clear and open, and the browser drops the selection on those.
- **`static/app.js` `drawItem` must stay in step with `item_point_on_canvas`** in `canvas_model.py` (translate, then rotate, then mirror). The R11 tests check only the Python side.
- **`canvas.template` still exists**, for old saves only. Don't remove it: old artwork with a template outline would lose that outline.
- **The real `saves/` folder holds the user's artwork.** It's git-ignored, and it must never be deleted, moved or changed.
- **Node isn't installed**, so `static/app.js` can't be syntax-checked with Node. Headless Edge works for this, at `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`. Use `--dump-dom` or `--screenshot`, with `--virtual-time-budget` so the page's scripts finish.
- **Git warns "LF will be replaced by CRLF".** This is harmless.
- **How this user works:** they also wanted the unrequested decisions written down (spec.md or a decision record), not just listed in chat. The rest is now in CLAUDE.md.
