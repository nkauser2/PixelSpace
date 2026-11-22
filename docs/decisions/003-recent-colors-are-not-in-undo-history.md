# 003: Picking a color is not part of undo/redo, clear, or saved artwork

Status: accepted (Round 2, R9)

## Decision (Y-statement)

In the context of **adding recent colors (R9) next to the existing undo/redo (R5), clear (R8) and save/open (R6) features**,
facing **the question of whether picking a color counts as a change to the artwork**,
we decided for **storing the recent colors separately from the `Canvas`, so undo, redo, clear and opening artwork never change them**,
and neglected **recording each color pick as an undoable step in the `Canvas` history, and saving the recent colors inside each artwork file**,
to achieve **undo that only steps through drawing actions (as it did in Round 1), and save files that stay exactly the same as in Round 1**,
accepting **that undo can't "un-pick" a color (the user just clicks another color instead)**.

## Alternatives considered

- **Color picks as undo steps:** pressing Undo after picking a color would appear to do nothing to the drawing, which would confuse beginners.
- **Recent colors saved with each artwork:** the user chose "only while running" for R9, and it would change the save file format.
