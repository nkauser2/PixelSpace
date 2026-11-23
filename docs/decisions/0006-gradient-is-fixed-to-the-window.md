# 0006: The pastel gradient is fixed to the window, not stretched over the page

Status: accepted (Round 4, R12)

## Decision (Y-statement)

In the context of **the lavender → soft pink → baby blue → mint green page background (R12)**,
facing **the fact that the page is often taller than the window (always on small screens, where the canvas and the left card stack on top of each other), so the gradient has to be fitted to either the window or the whole page**,
we decided for **a gradient fixed to the browser window (`background-attachment: fixed` with `min-height: 100vh` on `body`). The student always sees all four colors, from lavender in the top-left corner to mint green in the bottom-right, and the white canvas and left card scroll over it**,
and neglected **stretching the gradient over the full length of the page (it scrolls with the content), and repeating the gradient every window-height**,
to achieve **a background that always looks the same and always shows the whole lavender-to-mint range, however long the page is or however far the student has scrolled, with only two extra CSS lines and no JavaScript**,
accepting **that the background doesn't move when the page scrolls (a deliberate "parallax" look), and that some mobile browsers ignore `fixed` and treat it like a scrolling background. That only changes how the colors are spread out, not which colors are used or what stays white**.

## Alternatives considered

- **Stretch over the whole page (scrolls with the content):** the default browser behavior. On a long page (small screens), each window-height shows only a slice of the gradient. The top of the page would look mostly lavender and pink, and mint green would only show up at the very bottom. The four colors wouldn't be visible together.
- **Repeat the gradient every window-height:** all four colors appear in every screen, but there is a hard line where mint green suddenly jumps back to lavender. That looks like a mistake, not a soft pastel background.
