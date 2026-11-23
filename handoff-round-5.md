# Handoff: PixelSpace, end of Round 5

For a fresh session starting the next round. Read `CLAUDE.md` first for the standing rules. This file covers only the state at the end of Round 5. The earlier handoffs are still accurate for their rounds:
- `handoff-round-2.md`: R9, R10.
- `handoff-round-3.md`: R7, R11, and how items are stored in `strokes`.
- `handoff-round-4.md`: R12, and the CSS tests in `tests/test_style.py`.

## Current state

- **R1–R14 are implemented and tested.** Round 5 added:
  - **R13:** a dark purple deer's head with pink antlers over the canvas's top-right corner, also used as the browser tab icon.
  - **R14:** the deer is half size (32 px instead of 64 px) when the window is less than 600 px wide.
- **Only the page's look changed.** No Python, API, save-file or `app.js` changes. Old saves work as before.
- **Tests:** `python -m pytest` gives **348 passed** (Python 3.12.10, Flask 3.1.3): 331 from Round 4 plus 11 for R13 and 6 for R14. `LAST_REQUIREMENT` is 14.
- **Git:** branch `master`, last commit `4a8dcd9`, nothing pushed. Uncommitted: this file and a CLAUDE.md edit, waiting for the user.
- **Round 5 commits**, oldest first, each leaving all tests passing:
  - `836f4b5` (the user's): R13 and R14 in problem.md.
  - `10cbc4a`: spec.md Round 5 section.
  - `1627344`: R13. The deer file, page and CSS changes, `tests/test_icon.py`, `LAST_REQUIREMENT` raised to 13.
  - `d255773`: R14. The narrow-screen rule and its tests, `LAST_REQUIREMENT` raised to 14.
  - `9775857`: decision records 0007 and 0008. CLAUDE.md's next number moved to 0009.
  - `cd028ca`: 0007 no longer names an unchecked Safari version.
  - `a83744a`: README mentions the deer.
  - `beef135`, then `4a8dcd9`: spec.md's smaller-choices list, then the Round 5 section made more concise.

### What was added

- **`static/deer.svg`:** `viewBox="0 0 64 64"`, no background. Three groups:
  - `antlers`: pink stroke `#f472b6`;
  - `deer-body`: dark purple fill `#4c1d95`;
  - `face`: white eyes and a nose in `#2e1065`.
- **`templates/index.html`:**
  - `<link rel="icon" type="image/svg+xml">` pointing at the deer;
  - `<img class="deer-icon" alt="" draggable="false">` inside `canvas-wrap`, after the three canvases.
- **`static/style.css`:**
  - `.deer-icon`: absolute, `top`/`right` 8px, 64 × 64, `pointer-events: none`.
  - Directly after it, `@media (max-width: 599.98px)` sets it to 32 × 32 with a 4px gap.

### How the tests work

`tests/test_icon.py` reads the served `/`, `style.css` and `deer.svg`. It imports `rgb` and `strip_comments` from `test_style.py`. It adds `split_media` (keeps `@media` rules apart from always-on ones), `declarations` and `narrow_screen_rules`.

The tests check:
- the tab icon and canvas image use the same file;
- the image is inside `canvas-wrap`, after the canvases, in the top-right corner, with `pointer-events: none`;
- the body is dark purple, the antlers are pink, and nothing else is pink;
- the SVG has no background;
- "deer" and "icon" appear in neither save files nor `app.js`;
- the deer is 64 px at full size, and exactly half (size and gap) under a limit between 599.9 and 600 px.

## How to run

```
pip install -r requirements.txt
python app.py
```
Then open http://127.0.0.1:5000. Run the tests with `python -m pytest`. They save only into a temporary folder.

## Decisions made in Round 5, and why

**The user's answers** (asked before any code was written):
1. The deer goes over the canvas, inside the corner. It is never part of the artwork, and strokes can go under it.
2. 64 px, so 32 px on narrow screens.
3. "Narrow" means a window less than 600 px wide.

**Decision records:**
- **0007: one SVG file for the tab and the canvas.**
  - Rejected a PNG or `.ico` icon: it needs an image tool, gives two files that can drift apart, blurs when scaled, and tests can't check its colors.
  - Rejected inline `<svg>`: the tab icon can't point at it.
  - Cost: some browsers (older Safari in particular) may not show it, and there is no `/favicon.ico`.
- **0008: the deer is an `<img>` over the canvas, not painted on it.**
  - Rejected painting it on the canvas: the eraser and Clear would remove it, and it would be in the PNG.
  - Rejected a fourth canvas layer: it needs new `app.js` code.
  - Cost: the student can't see what they draw under the deer. That drawing is still saved and in the PNG.

**My smaller choices (in spec.md):**
- the deer's design and colors (the nose went from pink to purple so only the antlers are pink);
- the 8px / 4px gap;
- `599.98px`, so a zoomed 599.5 px window counts as narrow;
- `alt=""`;
- testing through the served files, plus headless Edge screenshots at 1300, 600 and 599 px;
- the README update.

## Unresolved

- **Nobody has seen the deer in a normal browser,** only in headless Edge, where it looked right.
- **The design and colors are my choice.** To change them, edit the three groups in `deer.svg`. The tests check purple and pink.
- **Dark tab bars:** the purple head may be hard to see; only the antlers stand out. I didn't add a background, because R13 didn't ask for one.
- **SVG tab icon support:** I didn't check which browser versions support it.
- **Still open from Round 3:**
  - Round 3's smaller choices are only in `handoff-round-3.md`. Most worth settling: picking a color switches to the brush only from the eraser, but spec.md line 27 still says it always switches.
  - Commit `90ed9bd` fails 3 tests on its own. It can't be fixed without amending.

## Warnings for the next session

- **Keep `pointer-events: none` on `.deer-icon`,** keep the deer inside `canvas-wrap` after the canvases, and keep `.canvas-wrap { position: relative }`.
- **The deer is a child of `canvasWrap`,** which has the pointer handlers in `app.js`. New code that loops over its children will find the `<img>`.
- **The R13 tests forbid "deer" and "icon" in `app.js` and save files.** If you need "icon" in `app.js` for something else, change that test to look for `deer.svg`/`deer-icon` instead.
- **`test_style.rule()` treats `@media` rules as always on.** Use `split_media` for new size or layout tests. Renaming `rgb` or `strip_comments` in `test_style.py` breaks `test_icon.py`.
- **The narrow rule must stay after `.deer-icon`** in `style.css`.
- **Edge's `--window-size` includes the scrollbar, and so do media queries,** so 599 and 600 really test both sides of the limit.
- **Earlier warnings still apply:**
  - Keep `.canvas-wrap`, `.panel` and `.btn` white, and the gradient on `body`.
  - Check `tool` in `strokes`; items are identified by their position in the list.
  - Keep `drawItem` in step with `item_point_on_canvas`, and don't remove `canvas.template`.
- **Never touch the real `saves/` folder.** It holds the user's artwork.
- **Git's "LF will be replaced by CRLF" warning is harmless.**
