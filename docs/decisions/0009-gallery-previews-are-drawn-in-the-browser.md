# 0009: Gallery previews are drawn in the browser from the saved strokes

Status: accepted (Round 6, R15)

## Decision (Y-statement)

In the context of **showing every saved artwork as a small preview in the gallery (R15)**,
facing **the rule that artwork saved in any earlier round must still open and look the same, and that those older save files only hold strokes, placed items and (before Round 3) a template name, with no picture inside them**,
we decided for **sending each artwork's checked strokes and template from a new `/api/gallery` route, and having `app.js` draw each preview on a small canvas with the same `drawStroke` and `drawTemplate` code that draws the real canvas, shrunk with `ctx.scale`**,
and neglected **making small PNG pictures on the server in Python, and storing a preview picture inside each save file when it is saved**,
to achieve **previews that look exactly like the artwork when it is opened, for every save file from every round, with no new dependency, no new field in save files, and no file ever written just by looking at the gallery**,
accepting **that the browser redraws every preview each time the gallery opens, so a folder with very many large drawings could take a moment to show, and that the previews can only be checked by tests that read `app.js` plus checks in a real browser (the project has no JavaScript test runner)**.

## Alternatives considered

- **PNG previews made on the server:** this needs an image library such as Pillow, which isn't in `requirements.txt` or installed on this computer. It would also need a second copy of all the drawing rules in Python (brush, eraser, letters in the browser's font, rotations and flips), which could drift from what the canvas shows.
- **A preview picture stored in each save file:** files saved before Round 6 have none, so they would still need another way to be drawn. Adding one would mean rewriting the user's old files or keeping two ways side by side. It would also make every save file bigger, and a stored picture could go out of date if the drawing code changes.

## Related detail

`/api/gallery` passes each file through `Canvas.from_dict`, the same check Open uses. A damaged file is listed with `"damaged": true` and drawn as a "Can't be shown" note instead of breaking the whole gallery. The file itself is not changed.
