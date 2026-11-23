# Handoff: PixelSpace, end of Round 7

For a fresh session starting the next round. Read `CLAUDE.md` first for the standing rules. This file covers only the state at the end of Round 7. The earlier handoffs are still accurate for their rounds:
- `handoff-round-2.md`: R9, R10.
- `handoff-round-3.md`: R7, R11, and how items are stored in `strokes`.
- `handoff-round-4.md`: R12, and the CSS tests in `tests/test_style.py`.
- `handoff-round-5.md`: R13, R14, and the CSS helpers in `tests/test_icon.py`.
- `handoff-round-6.md`: R15 (the gallery), and its warnings about `app.js` and `test_gallery.py`.

## Current state

- **R1–R16 are implemented and tested.** Round 7 added:
  - **R16:** the words "Welcome to PixelSpace" on their own line at the very top of the page, centered, in purple cursive, above the top bar.
- **Only the page's look changed.** No changes to `app.py`, `app.js`, `storage.py`, the Python models or save files. No new fields.
- **Tests:** `python -m pytest` gives **396 passed** (Python 3.12.10, Flask 3.1.3). That is 380 from Round 6, plus 16 in the new `tests/test_welcome.py`. `LAST_REQUIREMENT` is 16.
- **Git:** branch `master`, last commit `b6dd6cf`, nothing pushed. Uncommitted: this file and the CLAUDE.md edits, waiting for the user.
- **Round 7 commits**, oldest first, each leaving all tests passing:
  - `e83f523` (the user's): R16 in problem.md.
  - `7ad7f30`: spec.md Round 7 section, with the user's answers.
  - `4098500`: the message (`templates/index.html`, `static/style.css`), `tests/test_welcome.py`, `LAST_REQUIREMENT` raised to 16.
  - `c010a5f`: decision record 0011. CLAUDE.md's next number moved to 0012.
  - `a42072a`: README mentions the welcome message.
  - `b6dd6cf`: spec.md's list of smaller choices.

### What was added

- **`templates/index.html`:** `<p class="welcome">Welcome to PixelSpace</p>` is the first element inside `<body>` (after a comment), before `<header class="topbar">`. The top bar itself is unchanged.
- **`static/style.css`:**
  - A "welcome message (R16)" block just before the "top bar" block. `.welcome` has `text-align: center`, `font-family: "Segoe Script", "Brush Script MT", cursive`, `font-size: 2rem`, `color: var(--accent)` (`#7b4fd6`), and no background.
  - Inside the existing `@media (max-width: 599.98px)` block (the deer's R14 block): `.welcome { font-size: 1.5rem; }`.

### How the tests work

- `test_welcome.py` reads the served page and CSS. It turns `\r\n` into `\n` first.
- It imports `declarations` and `split_media` from `test_icon.py`, and `resolve`, `rgb` and `strip_comments` from `test_style.py`.
- `welcome_rules(css)` reads `.welcome` from the CSS **outside** any `@media` block. The narrow-screen size is allowed; a test checks that no `@media` block hides the message or changes its font.
- It checks the following:
  - the exact text, shown once;
  - that it's the first element in `<body>`, above and outside the top bar;
  - that the logo and buttons are still in the top bar;
  - centering and full width (no `position`, `width`, `max-width`, `float` or `display` on `.welcome`);
  - the font list in the chosen order, ending in `cursive`;
  - that nothing is loaded from outside (no `@font-face`, `@import`, outside `url(...)` or outside `<link href>`);
  - the accent purple, and no background;
  - that it's outside the canvas box and the gallery;
  - that `app.js` never contains "welcome";
  - that a save file contains neither "welcome" nor "cursive".

## How to run

```
pip install -r requirements.txt
python app.py
```
Then open http://127.0.0.1:5000. Run the tests with `python -m pytest`. They save only into a temporary folder.

## Decisions made in Round 7, and why

**The user's answers** (asked before any code was written):
1. The message goes on its own line above the top bar, centered. The logo and the Undo/Redo/Clear buttons stay.
2. Use cursive fonts already on the computer; download nothing.
3. The color is the accent purple, `#7b4fd6`.

**Decision record:**
- **0011: installed cursive fonts.** The font list is `"Segoe Script", "Brush Script MT", cursive`.
  - Rejected an online font service: it needs the internet on every load and goes against "no outside services".
  - Rejected a bundled font file: it would have to be downloaded, with its license checked, and the user chose not to.
  - Cost: the message may look a little different on other computers.

**My smaller choices (in spec.md):**
- the font order;
- a `<p>`, not a heading, so the logo stays the page's `<h1>`;
- 2rem, and 1.5rem under 600 px wide (the deer's limit), with 14 px of space above;
- wrapping onto two lines on very narrow windows;
- it scrolls away with the page (not fixed);
- the testing approach;
- the README update.

**Standing rules added to CLAUDE.md this round** (uncommitted, for the user to review):
- the welcome message is named as a page decoration;
- the page must work offline and never load fonts, scripts, stylesheets or pictures from the internet;
- how to check widths narrower than headless Edge allows (a local file with a frame of that width).

## How it was checked in a browser

I wrote a temporary script in the session's scratchpad (`create_app(save_dir=<temp folder>)` on port 5087). I used headless Edge with its own profile.
- **At 1300, 600 and 599 px wide:** the message is centered above the top bar, in Segoe Script, purple, on the gradient. It's smaller at 599 than at 600.
- **Below about 500 px:** headless Edge wouldn't make its window that narrow. The screenshot at `--window-size=360` was cut off on the right, top bar included, which is not how the page really looks.
- **In 360 px and 320 px wide frames:** I loaded a local HTML file (Windows `file:///C:/...` path) with two `<iframe>`s. The message fits on one line at 360 px and wraps onto two centered lines at 320 px.

The server was stopped afterwards. The real `saves/` folder was never used.

## Unresolved

- **Nobody has seen the message in a normal browser.** Only headless Edge has.
- **Other computers were not checked.** On a computer without Segoe Script or Brush Script MT, the browser picks its own `cursive` font, and it's not known which one.
- **The message wraps on screens narrower than about 340 px.** It reads fine, but it isn't on one line.
- **Still open from earlier rounds:**
  - Nobody has used the gallery in a normal browser. The "replace your drawing?" question from the gallery was not checked in a browser.
  - The gallery's speed with many or large artworks was not measured.
  - Keyboard focus is not kept inside the gallery pop-up.
  - A copied-in save file keeps its own `saved_at`.
  - Round 3's smaller choices are only in `handoff-round-3.md`. spec.md line 27 says picking a color always switches to the brush, but it only does so from the eraser.
  - Commit `90ed9bd` fails 3 tests on its own. It can't be fixed without amending.
  - The deer may be hard to see on dark tab bars.
  - SVG tab icon support in different browser versions was not checked.

## Warnings for the next session

- **`app.js` must not contain "welcome"** (R16 test). Earlier rounds also ban "deer" and "icon".
- **The message must stay the first element in `<body>`.** A test checks that the first tag after `<body>` (comments ignored) is exactly `<p class="welcome">`. Anything new placed above it, or a change to that tag (an extra attribute, for example), breaks the test.
- **Don't give `.welcome` a `position`, `width`, `max-width`, `float`, `display` or background outside `@media`.** The tests forbid them, to keep it a full-width, centered line on the gradient.
- **Don't start a second `@media (max-width: 599.98px)` block.** `split_media` in `test_icon.py` stores blocks in a dict keyed by their condition, so a second block with the same condition replaces the first, and the tests would only see one of them. Add narrow-screen rules to the existing block, as R16 did.
- **No outside files.** A test fails if the page `<link>`s to `http(s)://` or `//`, or if the CSS has `@font-face`, `@import` or an outside `url(...)`. A local `@font-face` would also fail it.
- **Headless Edge has a minimum window width of about 500 px.** Screenshots narrower than that are cut off, not real. Use frames (see CLAUDE.md).
- **Earlier warnings still apply** (see `handoff-round-6.md` for details):
  - `test_gallery.py` finds functions by name;
  - no `@media` block may mention `.gallery`;
  - keep `.gallery-backdrop[hidden] { display: none; }`;
  - the keydown handler returns early while the gallery is open;
  - keep `pointer-events: none` on the deer;
  - keep `.canvas-wrap`, `.panel` and `.btn` white, and the gradient on `body`;
  - don't remove `canvas.template`.
- **Bash heredocs with long text have failed before** without writing anything. The Write and Edit tools always worked.
- **Never touch the real `saves/` folder.** It holds the user's artwork.
- **Git's "LF will be replaced by CRLF" warning is harmless.**
