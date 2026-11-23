# 0007: One SVG file is both the browser tab icon and the deer on the canvas

Status: accepted (Round 5, R13 and R14)

## Decision (Y-statement)

In the context of **the dark purple deer with pink antlers that must sit on the canvas and also be the browser tab icon (R13), and be shown at half size on narrow screens (R14)**,
facing **the fact that browsers have traditionally used small `.ico` or `.png` files for tab icons, while the page needs the same deer at 64 px and 32 px, and Node or image tools aren't available to produce extra files**,
we decided for **a single hand-written SVG file, `static/deer.svg`, used by both `<link rel="icon" type="image/svg+xml">` and the `<img class="deer-icon">` on the canvas**,
and neglected **a PNG or `.ico` tab icon next to a separate picture for the page, and drawing the deer straight into the HTML as inline `<svg>` markup**,
to achieve **one picture that always looks the same in both places and stays sharp at any size (16 px tab, 64 px canvas, 32 px on narrow screens), that is a few lines of readable text a beginner can open and recolor, and that the tests can read to check the colors**,
accepting **that a few older browsers (for example Safari before version 26) don't show SVG tab icons and fall back to their default icon, and that there is no `/favicon.ico` file, so a browser that asks for it anyway gets a "not found" that it ignores**.

## Alternatives considered

- **PNG or `.ico` tab icon, plus a separate picture on the page:** this works in every browser, but needs an image tool to make it, gives two files that can drift apart when someone changes the colors, and looks blurry when scaled. It is also a binary file, so tests and people can't easily check that the deer is purple and the antlers are pink.
- **Inline `<svg>` written into index.html:** no extra request, but the tab icon can't point at it, so the deer would still need a second copy for the tab. It would also put ~20 lines of drawing code in the middle of the page layout.
