# 001: Keep the recent colors list in the Python server's memory

Status: accepted (Round 2, R9)

## Decision (Y-statement)

In the context of **showing the 5 most recently picked colors (R9)**,
facing **the need to test the "newest first, each color once, at most 5" rule automatically, and the user's choice that the list lasts only while the app runs**,
we decided for **keeping the list in a `RecentColors` object in the Flask server's memory, reached through `/api/recent-colors`**,
and neglected **keeping it only in the browser's JavaScript, and saving it in the browser's localStorage or a file on disk**,
to achieve **rules that are checked by the Python test suite like every other requirement, a list that survives reloading the page, and nothing extra written to disk**,
accepting **one small extra request to the server each time a color is picked, and the list being cleared whenever `python app.py` is restarted**.

## Alternatives considered

- **Browser JavaScript only:** no server code, but the project's tests are Python, so the R9 rules would go untested, and reloading the page would clear the list.
- **Browser localStorage:** survives restarts, which the user decided against, and it still can't be tested with pytest.
- **A file in saves/:** survives restarts (not wanted) and adds a file the user never asked for.
