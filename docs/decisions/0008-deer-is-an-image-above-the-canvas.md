# 0008: The deer is an image laid over the canvas, not painted onto it

Status: accepted (Round 5, R13)

## Decision (Y-statement)

In the context of **putting the deer in the canvas's top-right corner (R13), where the user chose "inside, over the canvas" and said it must never be part of the artwork and strokes can be drawn under it**,
facing **the fact that anything painted onto the drawing canvas becomes part of the picture: it would be erased by the eraser, wiped by Clear, and copied into the PNG download**,
we decided for **a plain `<img>` placed inside the canvas box, after (so above) the three canvas layers, with `position: absolute` in the top-right corner and `pointer-events: none` so every click and touch passes straight through it to the canvas**,
and neglected **painting the deer onto the paint layer or a new canvas layer with JavaScript, and placing the image without `pointer-events: none`**,
to achieve **a deer that is only decoration: drawing, erasing, placing and selecting all work in the corner as if it weren't there, and saving, undo, Clear and the PNG download are unchanged, with no change to `app.js` or the Python code**,
accepting **that the student can't see what they draw in the small area hidden under the deer (it is still there and shows up in the saved artwork and PNG), and that on a 32 px narrow-screen deer this area is very small**.

## Alternatives considered

- **Paint the deer onto the paint layer:** the eraser and Clear would remove it, and it would end up in every PNG download and need redrawing after undo, redo and opening artwork.
- **A fourth canvas layer drawn by JavaScript:** it would stay out of the artwork, but it needs new drawing code in `app.js`, must be redrawn when the canvas size changes, and can't share the tab icon's file as simply as an `<img>`.
- **An image that catches clicks:** without `pointer-events: none`, a stroke started on the deer would do nothing, which would make the corner of the canvas feel broken.
