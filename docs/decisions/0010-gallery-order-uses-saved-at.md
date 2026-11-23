# 0010: The gallery's "newest first" order uses the saved_at time inside each file

Status: accepted (Round 6, R15)

## Decision (Y-statement)

In the context of **ordering the gallery newest first (R15), where the user chose "newest" to mean the time an artwork was last saved, and renaming must not move it**,
facing **the fact that renaming (R10) rewrites the file to store the new name inside it, so the file's own "last modified" time changes on every rename**,
we decided for **sorting by the `saved_at` time that `save_artwork` has written into every save file since Round 1, newest first, with name order for artworks saved in the same second and files with no usable `saved_at` (such as damaged ones) at the end**,
and neglected **sorting by the file's last-modified time from the file system, and adding a new "created at" or "order" field to save files**,
to achieve **an order that only changes when the student saves, that works for every existing save file without changing it, and that tests can set up exactly by writing a chosen `saved_at`**,
accepting **that `saved_at` is the computer's local time with no time zone and only to the second, so artworks saved in the same second are ordered by name, and a save file copied in from somewhere else keeps its original save time**.

## Alternatives considered

- **The file's last-modified time:** renaming rewrites the file and would move the artwork to the front, which the user said must not happen. Copying or restoring files can also change it.
- **A new field for the order:** files from earlier rounds don't have it, and filling it in would mean changing the user's saved files.
