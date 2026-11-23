# PixelSpace

## What it does

PixelSpace is a beginner-friendly digital art canvas that runs in your web browser. You can draw freehand with a brush, erase, pick colors from a built-in palette or choose your own, and quickly reuse your 5 most recently picked colors. You can place shapes, letters and numbers in any color, then flip them or turn them 90° at a time. You can also undo, redo, clear the canvas, save your artwork to reopen later, and rename saved artwork. The page has a soft pastel background that fades from lavender to pink to baby blue to mint green, while the canvas stays white. A little dark purple deer with pink antlers sits in the canvas's top-right corner (smaller on narrow screens) and is also the icon in your browser tab. It is only decoration: you can draw underneath it, and it is never saved or included in your downloaded picture. Everything runs on your own computer, with no accounts, API keys or payments.

## How to run it

Install the requirements (one time only):

```
pip install -r requirements.txt
```

Start PixelSpace:

```
python app.py
```

Then open http://127.0.0.1:5000 in your web browser.

## How to run the tests

```
python -m pytest
```
