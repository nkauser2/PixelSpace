# Spec: Project 1: PixelSpace: 

PixelSpace is a digital art canvas/interface for students and beginner artists. Users can create digital artwork by drawing free-handedly on the interactive canvas. 

The application provides built-in colors, a drawing brush and eraser. It also has coloring templates. 

Users can also undo and redo their actions by clicking the specific buttons. 

Their artwork can also be saved and previously saved designs can be reopened. 

It works by implementing what the user chooses to do or picks and outputs information based on the user's input on the interface/canvas. 

It should be modern, beginner-friendly, but not extremely basic. 

It should run locally without accounts, external APIs or paid services/payments. 

# Round 2

Round 2 adds two features. Everything from Round 1 (R1-R8) keeps working.

## R9: Recent colors

- PixelSpace shows a "Recent colors" row with the 5 most recently picked colors, newest first.
- A color counts as "picked" when the user clicks a palette swatch, clicks a recent color, or finishes choosing with the custom color picker (the picker closes). The in-between shades shown while dragging inside the custom picker do not count.
- Each color appears only once. Picking a color that is already in the list moves it to the front.
- When a 6th different color is picked, the oldest one drops off the list.
- Clicking a recent color makes it the current brush color again (and switches to the brush, like the palette does).
- Colors are stored in the same standard form as strokes (e.g. "#ABC" becomes "#aabbcc"), so "#ABC" and "#aabbcc" count as the same color. Invalid colors are refused.
- The list starts empty when the app starts. It survives reloading the browser page, but not restarting `python app.py`. Nothing is written to disk.
- Picking a color is not a drawing action, so it is not part of undo/redo, and Clear does not empty the list.

## R10: Rename saved artwork

- In "My artwork", the user chooses a saved artwork, types a new name and clicks Rename.
- The artwork keeps all of its strokes and its template; only its name changes. The old name disappears from the saved list and the new name appears.
- New names are cleaned the same way as when saving (letters, numbers, spaces, dashes, underscores; spaces become "_").
- If the new name is already used by a different saved artwork, PixelSpace asks the user to confirm. Only if the user says yes is that other artwork replaced. If they say no, nothing changes.
- Renaming to the same name, or only changing upper/lower case (e.g. "cat" to "Cat"), is not treated as a clash with another artwork.
- Renaming an artwork that does not exist, or using a name with no letters or numbers, gives a clear error and changes nothing.
- If the renamed artwork is the one currently open, the name box updates to the new name.

# Round 3

Round 3 changes R7 and adds R11. Everything else (R1-R6, R8-R10) keeps working.

## R7 (changed): Shapes, letters and numbers to place

The coloring templates are replaced by items that students place on the canvas.

- The items are 8 shapes (circle, square, triangle, star, heart, diamond, hexagon, arrow), the capital letters A-Z and the digits 0-9.
- The student chooses an item in the "Shapes, letters & numbers" section, then clicks on the canvas. The item is placed with its center where they clicked.
- A placed item is a solid shape filled with the current color. Its size comes from the "Item size" slider (20-400, default 120). Its size and position don't change after it is placed.
- The item just placed becomes the "selected" item. The Select tool lets the student click any placed item to select it (the top one, if items overlap). The selected item has a dashed box around it. Choosing the brush or eraser, undo, redo, clear and opening artwork all clear the selection.
- Picking a color (palette, recent color, or closing the custom picker) while an item is selected re-colors that item. The color still counts as picked for Recent colors (R9).
- Placed items are part of the drawing. Brush strokes can paint over them, the eraser can erase them, and they are drawn in the order they were added.
- Placing an item and re-coloring it can each be undone and redone (R5). Clear removes all items (R8). Items are saved with the artwork and come back when it is reopened (R6).
- There is no template menu any more, so nothing new can use a template. Artwork saved in earlier rounds that uses a template still opens, and the template outline is still shown. Saving that artwork again keeps its template. Saved files are never changed just by opening them.

## R11: Flip and rotate

- Three buttons act on the selected item: "Flip ↔" (mirror left-right), "Flip ↕" (mirror top-bottom) and "Rotate 90°" (turn a quarter turn clockwise). They are disabled when no item is selected.
- Flips are always as seen on the screen. Flip ↔ swaps the item's left and right sides as they look now, even if it has been rotated.
- Four rotations bring an item back to how it started. Flipping twice the same way does too.
- The item turns or flips around its own center, so it stays in place.
- Each click is one step that can be undone and redone. Flips and rotations are saved with the artwork.

# Round 4

Round 4 adds R12. Everything else (R1-R11) keeps working, and nothing about drawing, saving or save files changes. R12 only changes how the page looks.

## R12: Pastel gradient background

- The page background is a soft pastel gradient instead of the plain (near-white) background. It runs diagonally, from **lavender** in the top-left corner, through **soft pink** and **baby blue**, to **mint green** in the bottom-right corner, in that order.
- The four colors are light pastels: lavender `#e6dcfa`, soft pink `#fcdde9`, baby blue `#d6e9fb`, mint green `#d5f5e3`. They are spread evenly (0%, 33%, 67%, 100%).
- The gradient covers the whole browser window, the top bar included. The top bar no longer has its own white strip. Its Undo, Redo and Clear buttons stay white so they are easy to read.
- **Not covered by the gradient (these stay white):**
  - the canvas, so artwork looks exactly as before and the downloaded PNG still has a white background;
  - the whole left card around the color palette (Tools, Colors, Shapes, letters & numbers, and My artwork), so every control stays easy to read.
- The gradient stays put while the page scrolls (it is fixed to the window), so it always fills the screen from lavender to mint, even on a small screen where the page is long.
- The gradient is never part of the artwork: it is not drawn on the canvas, not saved in save files, and not in the downloaded PNG.
