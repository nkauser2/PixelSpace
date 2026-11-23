# Claude.md : Project #1: 

Language: The program's main language will be Python. 

How the program is run: The user will start the application from the termminal (using python app.py) and access PixelSpace through their web browser. 

How the program is tested: Automated testing will be used and it will test the application's drawing logic, color selection, undo/redo functions, and saving ability. The user's interactions remain the core to how the application's functions work. 

What must never happen: Never use or require API keys, paid services/payments, or user accounts. Never delete saved artwork or do anything without the user's permission and approval. 

Decision records: Decision records in docs/decisions/ are numbered with four digits (0001, 0002, ...), and the next one is 0006.

Decision record format: Each decision record is written as a Y-statement (In the context of..., facing..., we decided for..., and neglected..., to achieve..., accepting...).

Requirements: Every requirement in problem.md is mandatory, and "should" means the same as "must". If a requirement is unclear, ask the user and wait for the answer before writing code.

Test names: Every test name starts with the requirement it checks, e.g. test_r9_... When new requirements are added, raise LAST_REQUIREMENT in tests/test_requirements_coverage.py.

Tests and saved artwork: Tests must only save into a temporary folder (the save_dir and client fixtures in tests/conftest.py), never into the real saves/ folder. storage.py must never have a delete or remove function.

Git: Commit in small steps with messages that say what changed and why. Never undo or amend a commit, and never push unless the user asks.
