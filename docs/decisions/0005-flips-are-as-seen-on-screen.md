# 0005: Flips mirror the item as it looks on screen, even after rotating

Status: accepted (Round 3, R11)

## Decision (Y-statement)

In the context of **the Flip ↔, Flip ↕ and Rotate 90° buttons for placed items (R11)**,
facing **the question of what "flip horizontally" should mean once an item has already been rotated, e.g. an "F" turned on its side**,
we decided for **flips that always mirror left-right or top-bottom as the student sees the item right now. In the code, a flip toggles `flip_x` or `flip_y` and also turns the rotation backwards (`rotation = 360 - rotation`)**,
and neglected **flipping along the item's own axes (just toggling `flip_x`/`flip_y` and leaving the rotation alone), and storing a full list of every flip and turn the student made**,
to achieve **buttons that do what their arrows show every time, which matters for beginners, and a saved item that is still described by just four values: rotation, flip_x, flip_y and its position**,
accepting **that the rotation number changes when you flip (so a flipped item's `rotation` isn't simply "how many times Rotate was clicked"), and that the browser must apply the steps in exactly the same order as `item_point_on_canvas` in canvas_model.py. The R11 tests check the on-screen result by moving real points around**.

## Alternatives considered

- **Flip along the item's own axes:** simpler code, but after one Rotate click, Flip ↔ would look like a top-bottom flip on screen. That's confusing for a beginner.
- **Keep a history of every flip and turn:** always exact, but the saved data grows with every click, and four flips or rotations no longer come back to the same saved values.
