# 0002: Rename by moving the save file in one step with os.replace

Status: accepted (Round 2, R10)

## Decision (Y-statement)

In the context of **renaming a saved artwork (R10)**,
facing **the rule that renaming must never lose the artwork, and CLAUDE.md's rule that saved artwork is never deleted without the user's permission**,
we decided for **moving the file to its new name with a single `os.replace`, then updating the name stored inside it with the existing write-to-temp-then-swap step**,
and neglected **copying to the new name and then deleting the old file, and saving a new copy while leaving the old file in place**,
to achieve **a rename that either fully happens or doesn't happen at all, with no delete function anywhere in storage.py (an existing test checks this)**,
accepting **that `os.replace` replaces a file that already has the new name, so the "ask before replacing" check has to happen first in our own code, and that a crash between the move and the name update leaves an out-of-date name inside the file (harmless, because the app goes by the file name)**.

## Alternatives considered

- **Copy, then delete the old file:** needs a delete step, which the project avoids. A crash in the middle could also leave two copies.
- **Save a new copy and keep the old one:** that isn't really renaming, and it fills the saved list with duplicates.

## Related detail

On Windows, `cat.json` and `Cat.json` are the same file. `os.path.samefile` is used so a case-only rename is not treated as a clash with another artwork.
