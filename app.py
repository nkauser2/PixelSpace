"""PixelSpace - a beginner-friendly digital art canvas.

Run it with:   python app.py
Then open:     http://127.0.0.1:5000  in your web browser.

This file is the web server. It shows the page and answers small JSON
requests from the browser (add a stroke, undo, save, ...). The real logic
lives in canvas_model.py, colors.py, shapes.py, storage.py and
coloring_templates.py.
"""

from flask import Flask, jsonify, render_template, request

import storage
from canvas_model import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    DEFAULT_ITEM_SIZE,
    MAX_ITEM_SIZE,
    MAX_SIZE,
    MIN_ITEM_SIZE,
    MIN_SIZE,
    Canvas,
)
from colors import DEFAULT_COLOR, PALETTE, RecentColors
from coloring_templates import get_template
from shapes import SHAPE_OUTLINES, list_items


def create_app(save_dir=None):
    """Build the Flask app. Tests pass their own `save_dir` (a temporary
    folder) so they never touch the user's real saved artwork."""
    app = Flask(__name__)
    save_dir = save_dir or storage.SAVE_DIR

    # PixelSpace runs locally for one person, so one canvas in memory is enough.
    app.config["CANVAS"] = Canvas()
    # Recent colors (R9) are kept only while the app runs, never on disk.
    # They live outside the Canvas, so undo, clear and opening artwork
    # don't change them.
    app.config["RECENT_COLORS"] = RecentColors()

    def canvas():
        return app.config["CANVAS"]

    def error(message, status=400):
        return jsonify({"error": message}), status

    def body():
        """The JSON sent by the browser (or an empty dict)."""
        data = request.get_json(silent=True)
        return data if isinstance(data, dict) else {}

    # ---- the page (R1) ---------------------------------------------------

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            palette=PALETTE,
            default_color=DEFAULT_COLOR,
            items=list_items(),
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            min_size=MIN_SIZE,
            max_size=MAX_SIZE,
            min_item_size=MIN_ITEM_SIZE,
            max_item_size=MAX_ITEM_SIZE,
            default_item_size=DEFAULT_ITEM_SIZE,
        )

    @app.get("/api/state")
    def get_state():
        return jsonify(canvas().state())

    # ---- drawing and erasing (R2, R3, R4) --------------------------------

    @app.get("/api/palette")
    def get_palette():
        return jsonify(PALETTE)

    @app.post("/api/stroke")
    def add_stroke():
        data = body()
        try:
            canvas().add_stroke(data.get("tool"), data.get("color"), data.get("size"), data.get("points"))
        except ValueError as e:
            return error(str(e))
        return jsonify(canvas().state())

    # ---- recent colors (R9) ---------------------------------------------

    @app.get("/api/recent-colors")
    def get_recent_colors():
        return jsonify(app.config["RECENT_COLORS"].colors)

    @app.post("/api/recent-colors")
    def pick_recent_color():
        recent = app.config["RECENT_COLORS"]
        try:
            recent.pick(body().get("color"))
        except ValueError as e:
            return error(str(e))
        return jsonify(recent.colors)

    # ---- undo / redo (R5) and clear (R8) ---------------------------------

    @app.post("/api/undo")
    def undo():
        canvas().undo()
        return jsonify(canvas().state())

    @app.post("/api/redo")
    def redo():
        canvas().redo()
        return jsonify(canvas().state())

    @app.post("/api/clear")
    def clear():
        canvas().clear()
        return jsonify(canvas().state())

    # ---- shapes, letters and numbers (R7) ---------------------------------

    @app.get("/api/items")
    def items_list():
        """Every item; shapes also carry the outline the browser fills in."""
        items = list_items()
        for item in items:
            if item["kind"] == "shape":
                item["points"] = SHAPE_OUTLINES[item["id"]]
        return jsonify(items)

    @app.post("/api/item")
    def place_item():
        data = body()
        try:
            index = canvas().place_item(data.get("item"), data.get("color"), data.get("size"), data.get("x"), data.get("y"))
        except ValueError as e:
            return error(str(e))
        # The item just placed becomes the selected one.
        return jsonify({**canvas().state(), "selected": index})

    @app.post("/api/item/recolor")
    def recolor_item():
        data = body()
        try:
            canvas().recolor_item(data.get("index"), data.get("color"))
        except ValueError as e:
            return error(str(e))
        return jsonify(canvas().state())

    @app.post("/api/item-at")
    def item_at():
        """Which item is under the pointer? Used by the Select tool."""
        data = body()
        try:
            index = canvas().item_at(data.get("x"), data.get("y"))
        except ValueError as e:
            return error(str(e))
        return jsonify({"index": index})

    # ---- flip and rotate (R11) -------------------------------------------

    @app.post("/api/item/rotate")
    def rotate_item():
        try:
            canvas().rotate_item(body().get("index"))
        except ValueError as e:
            return error(str(e))
        return jsonify(canvas().state())

    @app.post("/api/item/flip")
    def flip_item():
        data = body()
        try:
            canvas().flip_item(data.get("index"), data.get("direction"))
        except ValueError as e:
            return error(str(e))
        return jsonify(canvas().state())

    # ---- template outlines in artwork saved before Round 3 (R7) ----------
    # Templates can't be chosen any more, but old saves that use one still
    # show its outline, so the browser can still fetch it.

    @app.get("/api/templates/<template_id>")
    def template_detail(template_id):
        template = get_template(template_id)
        if template is None:
            return error(f"No template called '{template_id}'.", 404)
        return jsonify(template)

    # ---- saving and reopening (R6) ---------------------------------------

    @app.get("/api/saves")
    def saves_list():
        return jsonify(storage.list_artworks(save_dir))

    @app.post("/api/save")
    def save():
        data = body()
        try:
            name = storage.save_artwork(
                canvas().to_dict(), data.get("name"), save_dir, overwrite=data.get("overwrite") is True
            )
        except storage.ArtworkExistsError as e:
            # 409 tells the browser to ask the user before replacing it.
            return jsonify({"error": str(e), "exists": True}), 409
        except ValueError as e:
            return error(str(e))
        return jsonify({"saved": name})

    # ---- renaming saved artwork (R10) -------------------------------------

    @app.post("/api/rename")
    def rename():
        data = body()
        try:
            new_name = storage.rename_artwork(
                data.get("old_name"), data.get("new_name"), save_dir, overwrite=data.get("overwrite") is True
            )
        except storage.ArtworkExistsError as e:
            # 409 tells the browser to ask the user before replacing it.
            return jsonify({"error": str(e), "exists": True}), 409
        except FileNotFoundError as e:
            return error(str(e), 404)
        except ValueError as e:
            return error(str(e))
        return jsonify({"renamed": new_name})

    @app.post("/api/load")
    def load():
        try:
            data = storage.load_artwork(body().get("name"), save_dir)
            app.config["CANVAS"] = Canvas.from_dict(data)
        except FileNotFoundError as e:
            return error(str(e), 404)
        except ValueError as e:
            return error(str(e))
        return jsonify(canvas().state())

    return app


if __name__ == "__main__":
    print("PixelSpace is running! Open http://127.0.0.1:5000 in your browser.")
    print("Press Ctrl+C here to stop it.")
    create_app().run(host="127.0.0.1", port=5000, debug=False)
