# Handoff: PixelSpace, end of Round 6

For a fresh session starting the next round. Read `CLAUDE.md` first for the standing rules. This file covers only the state at the end of Round 6. The earlier handoffs are still accurate for their rounds:
- `handoff-round-2.md`: R9, R10.
- `handoff-round-3.md`: R7, R11, and how items are stored in `strokes`.
- `handoff-round-4.md`: R12, and the CSS tests in `tests/test_style.py`.
- `handoff-round-5.md`: R13, R14, and the CSS helpers in `tests/test_icon.py`.

## Current state

- **R1–R15 are implemented and tested.** Round 6 added:
  - **R15:** a "🖼️ Gallery" button in "My artwork". It opens a pop-up over the page with a small preview of every saved artwork, five per row on every screen size, newest saved first. Clicking a preview opens that artwork.
- **Save files did not change.** No new fields. The gallery only reads them. Old saves (including ones with a template) show in the gallery and open as before.
- **Tests:** `python -m pytest` gives **380 passed** (Python 3.12.10, Flask 3.1.3). That is 348 from Round 5, plus 32 for R15:
  - 9 in `tests/test_storage.py`;
  - 7 in `tests/test_app.py`;
  - 16 in the new `tests/test_gallery.py`.
  `LAST_REQUIREMENT` is 15.
- **Git:** branch `master`, last commit `0b9fa22`, nothing pushed. Uncommitted: this file and CLAUDE.md edits, waiting for the user.
- **Round 6 commits**, oldest first, each leaving all tests passing:
  - `a86cdf9` (the user's): R15 in problem.md.
  - `8804f8c`: spec.md Round 6 section, with the user's answers.
  - `0a278cb`: `storage.gallery_artworks`, the `/api/gallery` route, their tests, `LAST_REQUIREMENT` raised to 15.
  - `61cf93b`: the button, the pop-up, the previews (HTML, CSS, `app.js`) and `tests/test_gallery.py`.
  - `83c6dbd`: decision records 0009 and 0010. CLAUDE.md's next number moved to 0011.
  - `9448ebf`: README mentions the gallery.
  - `0b9fa22`: spec.md's list of smaller choices.

### What was added

- **`storage.py`:** `gallery_artworks(save_dir)` returns `[{"name", "saved_at", "artwork"}]`.
  - It is newest `saved_at` first. Equal times are in name order, and a missing or unreadable `saved_at` goes last.
  - `artwork` is the file's data, or `None` for a damaged file.
  - It only reads files. `_is_save_time` checks `saved_at` with `datetime.fromisoformat`.
- **`app.py`:** `GET /api/gallery` gives `[{"name", "saved_at", "damaged", "template", "strokes"}]`, in the order above.
  - Each artwork goes through `Canvas.from_dict(...).to_dict()`, the same check Open uses.
  - A file that fails the check gets `damaged: true`, `strokes: []`, `template: null`.
  - It changes nothing: not the canvas, the undo history, or any file.
- **`templates/index.html`:**
  - `#gallery-btn` sits in "My artwork", above Download.
  - `<div id="gallery" class="gallery-backdrop" hidden>` comes after `</main>` and before the toast. Inside it are `#gallery-close`, `#gallery-empty` (hidden) and `#gallery-grid`.
- **`static/style.css`:** a "gallery of saved artwork (R15)" block at the end.
  - `.gallery-backdrop` is fixed, `inset: 0`, `z-index: 50`.
  - `.gallery-backdrop[hidden] { display: none; }`.
  - `.gallery-grid` is `repeat(5, minmax(0, 1fr))`.
  - `.gallery-preview` has a white background.
  - `.toast` got `z-index: 60`.
- **`static/app.js`:**
  - `getTemplate(id)` and `drawTemplate(ctx, template)` were split out of `showTemplate`, so previews use them too.
  - `openArtwork(name)` is shared by the Open button and the gallery. It asks before replacing a drawing, returns true or false, and also sets `openSelect.value`.
  - The gallery section has `PREVIEW_WIDTH = 200`, `drawPreview`, `makeGalleryCard`, `openGallery`, `closeGallery` and `openFromGallery`.
  - The keydown handler starts with: while the gallery is open, Escape closes it and nothing else runs.
  - `const outlinesReady = loadShapeOutlines();` is in the start section. `openGallery` awaits it, so placed shapes have their outlines.

### How the tests work

- `test_storage.py` writes save files with a chosen `saved_at` (`write_save`) to test the order.
- `test_app.py` checks `/api/gallery` against `/api/load`. It also checks damaged files, old template saves, and that nothing changes.
- `test_gallery.py` reads the served page, CSS and `app.js`:
  - It imports `declarations` and `split_media` from `test_icon.py`, and `background_of`, `is_white` and `strip_comments` from `test_style.py`.
  - `function_body(script, name)` finds `function name(` up to the next line that is just `}`. The `script` fixture turns `\r\n` into `\n` first.
  - It checks that no `@media` block mentions `.gallery`, which is how "always five per row" is tested.

## How to run

```
pip install -r requirements.txt
python app.py
```
Then open http://127.0.0.1:5000. Run the tests with `python -m pytest`. They save only into a temporary folder.

## Decisions made in Round 6, and why

**The user's answers** (asked before any code was written):
1. "Most latest first" means the time the artwork was last saved. Renaming doesn't move it.
2. The gallery is a pop-up over the page, not a separate page.
3. Clicking a preview opens it right away (asking first if the canvas has a drawing, like Open).
4. Always five per row, even under 600 px wide.

**Decision records:**
- **0009: previews are drawn in the browser** from the saved strokes, with the canvas's own `drawStroke` and `drawTemplate`, shrunk with `ctx.scale`.
  - Rejected server-made PNGs: they need Pillow (not installed, not in `requirements.txt`) and a second copy of the drawing rules in Python.
  - Rejected a preview picture stored in save files: older saves have none, and it would mean changing the user's files.
  - Cost: every preview is redrawn each time the gallery opens, and previews can only be tested by reading `app.js` plus browser checks.
- **0010: the order uses `saved_at`** inside each file.
  - Rejected the file's modified time: renaming rewrites the file (`_update_name_inside`), so a renamed artwork would jump to the front.
  - Rejected a new order field: it would mean changing old files.
  - Cost: `saved_at` is local time to the second, so same-second saves are in name order.

**My smaller choices (in spec.md):**
- damaged files show as a "Can't be shown" card that can't be clicked, and they go last;
- the name under each preview is cut off with "…", with the full name in the tooltip;
- the button is placed above Download;
- Escape, a click on the dark backdrop, or Close shuts the pop-up, and shortcuts are off while it's open;
- saying no to the replace question keeps the gallery open;
- opening from the gallery selects that artwork in the saved list;
- toasts show above the pop-up;
- the gallery is re-fetched on every open;
- previews are 200 × 150 inside;
- the testing approach;
- the README update.

**Standing rules added to CLAUDE.md this round** (uncommitted, for the user to review):
- tests that read files must turn `\r\n` into `\n`;
- old saves must also look the same in the gallery, and only saving or renaming may write to a save file;
- how to check a click with headless Edge (a temporary route in a script outside the project);
- page decorations must not be in gallery previews either.

## How it was checked in a browser

I wrote a temporary script outside the project (`create_app(save_dir=<temp folder>)` on port 5077). It made 7 artworks with different `saved_at` times, one with a rotated letter and an eraser stroke, one old save with the `flower` template, and one damaged file. It also added two routes that serve the page with a script that clicks the Gallery button, and then the first preview.

Headless Edge, with its own profile, showed:
- at 1300, 600 and 599 px wide: five per row, newest first, the eraser gap, the flower outline, the damaged card, and no deer or gradient in any preview;
- after a click on the first preview, the page title read `RESULT art7 hidden=true strokes=2`. So the newest artwork opened and the gallery closed.

The server was stopped afterwards. The real `saves/` folder was never used.

## Unresolved

- **Nobody has used the gallery in a normal browser.** Only headless Edge has seen it.
- **The "replace your drawing?" question from the gallery was not checked in a browser.** The click check started from an empty canvas, so no question appeared. The code path is the same `openArtwork` the Open button uses.
- **Speed with many or large artworks was not measured.** `/api/gallery` sends every stroke of every artwork, and every preview is redrawn on each open.
- **Keyboard focus is not kept inside the pop-up.** Tab can move to buttons behind it. Focus goes to Close when it opens, and back to the Gallery button when it closes.
- **A copied-in save file keeps its own `saved_at`,** so it may not appear first.
- **Still open from earlier rounds:**
  - Round 3's smaller choices are only in `handoff-round-3.md`. spec.md line 27 says picking a color always switches to the brush, but it only does so from the eraser.
  - Commit `90ed9bd` fails 3 tests on its own. It can't be fixed without amending.
  - The deer may be hard to see on dark tab bars.
  - SVG tab icon support in different browser versions was not checked.

## Warnings for the next session

- **`app.js` must still not contain "deer" or "icon"** (R13 tests). The gallery code avoids both words.
- **`test_gallery.py` finds functions by name.** Renaming `openGallery`, `drawPreview`, `makeGalleryCard`, `openArtwork` or `openFromGallery`, or changing lines it looks for, breaks those tests. Change the tests in the same commit if you must.
- **No `@media` block may mention `.gallery`.** That is how "five per row on every screen" is tested.
- **Keep `.gallery-backdrop[hidden] { display: none; }`.** Without it, `display: flex` shows the pop-up even while it is hidden, and it would cover the canvas.
- **The keydown handler returns early while the gallery is open.** New shortcuts must go after that check.
- **`outlinesReady` is a `const` in the start section at the bottom of `app.js`.** Don't call `openGallery` before that line runs.
- **Opening goes through `openArtwork`.** A change to how Open behaves changes the gallery too.
- **Preview drawing relies on the eraser cutting through to the preview's white CSS background** (`destination-out`). Don't paint a white rectangle first, or eraser marks would disappear from previews.
- **New fields in save files** must also pass through `Canvas.from_dict` if previews need them. `/api/gallery` only sends what `to_dict()` returns.
- **Earlier warnings still apply:**
  - keep `pointer-events: none` on the deer;
  - keep `.canvas-wrap`, `.panel` and `.btn` white, and the gradient on `body`;
  - check `tool` in `strokes`;
  - keep `drawItem` in step with `item_point_on_canvas`;
  - don't remove `canvas.template`.
- **In this session, Bash heredocs with long multi-line text sometimes failed** ("unexpected EOF while looking for matching `'`") without writing anything. The Write and Edit tools worked every time.
- **Never touch the real `saves/` folder.** It holds the user's artwork.
- **Git's "LF will be replaced by CRLF" warning is harmless.**
