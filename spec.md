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
