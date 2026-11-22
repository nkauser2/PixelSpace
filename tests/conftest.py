"""Shared test helpers.

Every test that saves artwork uses pytest's `tmp_path` (a brand-new temporary
folder), so the tests can never touch the user's real saves/ folder.
"""

import pytest


@pytest.fixture
def save_dir(tmp_path):
    return tmp_path / "saves"


@pytest.fixture
def client(save_dir):
    # Imported here (not at the top) so tests that don't need the web app
    # can run on their own.
    from app import create_app

    app = create_app(save_dir=save_dir)
    app.config["TESTING"] = True
    return app.test_client()


def brush(points=None, color="#e63946", size=8):
    """A ready-made brush stroke for tests."""
    return {"tool": "brush", "color": color, "size": size, "points": [[10, 10], [20, 20]] if points is None else points}


def eraser(points=None, size=20):
    """A ready-made eraser stroke for tests."""
    return {"tool": "eraser", "color": None, "size": size, "points": [[10, 10], [20, 20]] if points is None else points}
