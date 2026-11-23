# Handoff: PixelSpace, end of Round 4

This is for a fresh session starting the next round. Read `CLAUDE.md` first: it has the standing rules for every session. This file only covers what is true at the end of Round 4. The earlier handoffs still describe their rounds accurately:
- `handoff-round-2.md`: R9 recent colors, R10 rename.
- `handoff-round-3.md`: R7 placeable items, R11 flip/rotate. It also explains how items are stored in `strokes`.

## Current state

- **Every requirement R1–R12 is implemented and tested.** Round 4 added one requirement:
  - **R12 (new):** the page background is a diagonal pastel gradient, lavender → soft pink → baby blue → mint green. It covers the whole window, including the top bar. The canvas and the whole left card (Tools, Colors, Shapes, My artwork) stay white.
- **R12 only changed how the page looks.** No Python code, API route, save-file field or `app.js` code changed in Round 4. Drawing, saving and old saves all work as in Round 3.
- **Tests:** `python -m pytest` gives **331 passed** (Python 3.12.10, Flask 3.1.3). That is 320 from Round 3 plus 11 new R12 tests. `LAST_REQUIREMENT` is 12.
- **Git:** branch `master`, last commit `95cfa9f`. Nothing has been pushed. Uncommitted: this file and a CLAUDE.md edit, both waiting for the user to read them.
- **Round 4 commits**, oldest first. Every one leaves all tests passing:
  - `ceb627c` (the user's own commit): R12 added to problem.md.
  - `ff8efe7`: spec.md Round 4 section.
  - `15f10b4`: the gradient in `static/style.css`, the new `tests/test_style.py`, and `LAST_REQUIREMENT` raised to 12.
  - `976e7ca`: decision record 0006. The CLAUDE.md "next one is" number was moved to 0007.
  - `29432b7`: README mentions the background.
  - `95cfa9f`: spec.md "Smaller choices made in Round 4" list.

### What changed in `static/style.css`

- New variables in `:root`:
  - `--bg-lavender` `#e6dcfa`
  - `--bg-pink` `#fcdde9`
  - `--bg-blue` `#d6e9fb`
  - `--bg-mint` `#d5f5e3`
  - `--page-gradient`: `linear-gradient(to bottom right, …0%, 33%, 67%, 100%)`
- The old `--bg: #f4f2fb` was removed.
- `body` now has `min-height: 100vh`, `background: var(--page-gradient)` and `background-attachment: fixed`.
- `.topbar` now has `background: transparent` and a faint white bottom border, `rgba(255,255,255,0.6)`.
- Unchanged, and required by R12:
  - `.panel` (the left card) still uses `var(--panel)`, which is `#ffffff`.
  - `.canvas-wrap` still uses `#fff`.
  - `.btn` still uses `var(--panel)`, so the top bar buttons stay white.

### Where things are (unchanged from Round 3 except where noted)

| File | What it holds |
|---|---|
| `app.py` | Flask server: `create_app(save_dir=None)` and the JSON API under `/api/...` |
| `canvas_model.py` | `Canvas`: strokes and placed items, undo/redo, clear, flip/rotate |
| `shapes.py` | The 44 placeable items |
| `coloring_templates.py` | Template outlines, only for artwork saved in Rounds 1–2 |
| `colors.py` | Palette, hex checks, `RecentColors` |
| `storage.py` | Save, list, load, rename. Files go in `saves/*.json` |
| `templates/index.html`, `static/app.js`, `static/style.css` | The browser page. **Round 4 changed only `style.css`** |
| `tests/test_style.py` | **New.** R12 tests that read the served stylesheet |
| `docs/decisions/` | 0001–0003 (Round 2), 0004–0005 (Round 3), **0006 (Round 4)** |
| `spec.md` | Original spec plus Round 2, 3 and 4 sections |

### How the R12 tests work

`tests/test_style.py` fetches `/static/style.css` through the `client` fixture. It has small helpers:
- `rule(css, selector)` gives the declarations for exactly that selector. Later rules win.
- `variables(css)` gives the `:root` variables.
- `resolve(css, value)` replaces `var(--x)` with the variable's value, including variables inside other variables.
- `background_of(css, selector)` gives the selector's background with all variables replaced.

The tests check:
- the four colors are present, in order, and the gradient runs `to bottom right`;
- each color is a light pastel that matches its name (for example, lavender has red > green and blue > green);
- the gradient fills the window (`margin: 0`, `min-height: 100vh`, `background-attachment: fixed`);
- the top bar is `transparent`;
- the buttons, canvas and left card are white;
- the palette and recent colors are inside `<aside class="panel">`;
- a save file contains no "gradient" or "background".

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
The tests save only into a temporary folder, through the `save_dir` and `client` fixtures in `tests/conftest.py`.

## Decisions made in Round 4, and why

### The user's answers to my questions (asked before any code was written)

R12 says "cover whole page except for canvas and surrounding color palette", which could be read more than one way. I asked three questions:
1. **What stays white:** the **whole left card**, not only the Colors section, so every control stays easy to read.
2. **Top bar:** it **shows the gradient**, to match "cover whole page". Its buttons stay white.
3. **Direction:** **diagonal**, with lavender in the top-left and mint green in the bottom-right.

### Recorded in docs/decisions/

- **0006: the gradient is fixed to the window** (`background-attachment: fixed`). I rejected stretching it over the whole page: on small screens, where the page is long, you'd only ever see a slice of it. I also rejected repeating it, which leaves a hard mint-to-lavender line. Some mobile browsers ignore `fixed`.

### Written in spec.md (Round 4 section and its "Smaller choices" list)

- The exact four colors and their even spread. I picked these; problem.md only names the colors.
- The gradient is not drawn on the canvas, saved, or included in the downloaded PNG. The PNG download in `app.js` already paints its own white background.
- The top bar's grey bottom line became a faint white line.
- Disabled Undo/Redo keep their 40% opacity, so a little of the gradient shows through them.
- The tip line under the canvas keeps its grey text, now on the gradient.
- The old `#f4f2fb` page color was removed.
- R12 is tested through the CSS text, and checked by eye in headless Edge screenshots at 1300×900 and 600×900.
- The README now mentions the background.

## Unresolved

- **Nobody has looked at the gradient in a normal browser yet.** It was only seen in headless Edge screenshots. In those, both window sizes looked right: soft colors, the canvas and left card white, and the text readable.
- **The color values are my choice.** The user may want them lighter, stronger or different. Changing them means editing only the four `--bg-*` variables. The R12 tests will catch a color that is too dark, too grey, or no longer matches its name.
- **Still open from Round 3:** the user was asked whether Round 3's smaller choices should be added to spec.md. I found no answer in the repo, and those choices are still only in `handoff-round-3.md`, under "Smaller choices not written in spec.md or a decision record". The one most worth settling is that picking a color now switches to the brush only when the eraser is in use. This changes Round 1–2 behavior, and spec.md line 27 (R9) still says that clicking a recent color "switches to the brush".
- **Commit `90ed9bd` (Round 3) fails 3 page tests on its own.** It can't be fixed without amending, which isn't allowed.

## Warnings for the next session

- **Keep the canvas and the left card white.** R12 depends on `.canvas-wrap`, `.panel` and `.btn` staying white. If you restyle those, or move the palette out of `<aside class="panel">`, the R12 tests will fail, and so will the requirement.
- **The R12 tests read CSS text with simple regexes.** They expect one plain `selector { ... }` rule per selector, and the `background` (or `background-color`) property. A rule inside an `@media` block is read as if it always applied, so a small-screen `body` or `.panel` background there would fool them. They also don't look at `background-image`, so a gradient written that way won't be found. If you restructure `style.css`, check `tests/test_style.py`'s helpers still find the rules.
- **The background is set on `body`, not `html`.** The browser spreads the `body` background to the whole window because `html` has none. Giving `html` a background would break this.
- **All Round 3 warnings still apply:**
  - Not everything in `strokes` is a stroke. Check `tool`.
  - Items are identified by their position in the list.
  - `drawItem` in `app.js` must stay in step with `item_point_on_canvas`.
  - Don't remove `canvas.template`.
- **The real `saves/` folder holds the user's artwork.** It's git-ignored, and it must never be deleted, moved or changed.
- **Git warns "LF will be replaced by CRLF".** This is harmless.
