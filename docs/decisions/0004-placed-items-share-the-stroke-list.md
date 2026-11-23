# 0004: Placed items go in the same ordered list as brush and eraser strokes

Status: accepted (Round 3, R7 and R11)

## Decision (Y-statement)

In the context of **letting students place shapes, letters and numbers on the canvas (R7) and flip or rotate them afterwards (R11)**,
facing **the need for items to work with the brush, eraser, undo/redo, clear and save/open that already exist, and for artwork saved in Rounds 1-2 to keep opening**,
we decided for **storing each placed item as an entry with `"tool": "item"` in the canvas's existing ordered `strokes` list, drawn in order with the strokes**,
and neglected **a separate `items` list drawn above or below all the strokes, and "stamping" items into fixed brush-like marks that can't be changed once placed**,
to achieve **items that the brush can paint over and the eraser can erase, just like everything else on the canvas; undo/redo, clear and saving that work for items with no new code; and save files that Rounds 1-2 can still read in the same format**,
accepting **that the list is still called `strokes` even though it now holds items too, that every piece of code reading the list must check `tool` before using stroke-only or item-only fields, and that an item is identified by its position in the list (so the browser drops its selection after undo, redo, clear or open)**.

## Alternatives considered

- **Separate `items` list, drawn on top of all strokes:** brush strokes could never cover an item, so a student couldn't paint a pattern over a star, and the eraser couldn't touch items. This adds a second list to undo, clear and save.
- **Separate `items` list, drawn under all strokes:** placing a star on top of a painted background would hide it under the paint.
- **Stamp items into fixed marks:** the simplest to draw, but an item couldn't be selected, re-colored, flipped or rotated after placing, which R11 needs.
- **Rename `strokes` to something like `marks`:** clearer, but every saved artwork file and many existing tests use `strokes`, so old saves would need converting.
