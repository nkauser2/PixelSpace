# Claude.md : Project #1: 

Language: The program's main language will be Python. 

How the program is run: The user will start the application from the termminal (using python app.py) and access PixelSpace through their web browser. 

How the program is tested: Automated testing will be used and it will test the application's drawing logic, color selection, undo/redo functions, and saving ability. The user's interactions remain the core to how the application's functions work. 

What must never happen: Never use or require API keys, paid services/payments, or user accounts. Never delete saved artwork or do anything without the user's permission and approval. 

Decision records: Decision records in docs/decisions/ are numbered with four digits (0001, 0002, ...), and the next one is 0012.

Decision record format: Each decision record is written as a Y-statement (In the context of..., facing..., we decided for..., and neglected..., to achieve..., accepting...).

Requirements: Every requirement in problem.md is mandatory, and "should" means the same as "must". If a requirement is unclear, ask the user and wait for the answer before writing code.

Test names: Every test name starts with the requirement it checks, e.g. test_r9_... When new requirements are added, raise LAST_REQUIREMENT in tests/test_requirements_coverage.py.

Tests that read files: The project's files can have Windows line endings (\r\n). A test that searches the text of app.js, the page or another file with a pattern that spans lines must turn "\r\n" into "\n" first.

Tests and saved artwork: Tests must only save into a temporary folder (the save_dir and client fixtures in tests/conftest.py), never into the real saves/ folder. storage.py must never have a delete or remove function.

Old saves: Artwork saved in any earlier round must still open and look the same, both on the canvas and in the gallery's previews. Only saving or renaming may write to a save file; listing, opening or showing artwork (such as the gallery) only reads it. Don't rename or change the meaning of fields in save files (such as "strokes" and "template"). Only add new ones.

Checking in a browser: When running the app to check the page, start it with a temporary save folder (create_app(save_dir=...)) on a spare port, never against the real saves/ folder. If you use headless Edge, give it its own temporary profile (--user-data-dir), not the user's browser profile. Node isn't installed on this computer, so use headless Edge (C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe) with --screenshot or --dump-dom and --virtual-time-budget so the page's scripts finish. Stop the temporary server when you're done. When opening a local file in Edge, use a Windows path (file:///C:/...), not a Git Bash path (/c/...), or the file won't load. For a requirement that depends on screen size, take screenshots on both sides of the limit (for example 599 and 600 px wide). Headless Edge can't click, so to check what a click does, write a temporary script outside the project that adds an extra route serving the page with a small script that clicks for you (and writes the result into the page title for --dump-dom). Never add such a route to app.py.

Page decorations: Anything that only decorates the page (such as the pastel background and the deer icon) must never become part of the artwork. It must not be drawn on the canvas, saved in save files, included in the downloaded PNG, or shown in the gallery's previews, and it must never stop the student drawing on any part of the canvas.

Facts in docs: Only write facts you have checked (such as browser support or version numbers) in spec.md, decision records, the README or handoff files. If you haven't checked something, say so.

Handoff files: Write a round's handoff file (handoff-round-N.md) only when the user asks for it. Don't commit the handoff file, or the CLAUDE.md changes written with it; the user reads and edits them first.

Decisions: At the end of each round, list every decision the user did not ask for, and record them in spec.md or a decision record, not only in the chat.

Git: Commit in small steps with messages that say what changed and why. Every commit should leave all tests passing. Never undo or amend a commit, and never push unless the user asks.
