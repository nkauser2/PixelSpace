# 0011: The welcome message uses cursive fonts already on the computer

Status: accepted (Round 7, R16)

## Decision (Y-statement)

In the context of **writing "Welcome to PixelSpace" in cursive at the top center of the page (R16), in an app that must run locally with no outside services, built only from what is in this repository**,
facing **the fact that the repository has no font files, that a web font from an online font service would need an internet connection every time the page loads, and that the user chose "fonts already on the computer" over bundling a font file**,
we decided for **a CSS font list of fonts that are already installed: `"Segoe Script", "Brush Script MT", cursive`, where the browser uses the first one it has and the generic `cursive` font is the last fallback**,
and neglected **loading a font from an online font service, and adding a free-licensed cursive font file to `static/` with `@font-face`**,
to achieve **a message that shows in cursive straight away, works with no internet connection, adds no files or downloads, and keeps the "no outside services" rule; tests can check it just by reading the stylesheet**,
accepting **that the message may look a little different on other computers. Segoe Script and Brush Script MT were checked to be installed on this Windows 11 PC (in `C:\Windows\Fonts`), and the page was checked in headless Edge here, where Segoe Script was used. Which fonts other systems have, and which font a browser picks for `cursive`, was not checked.**

## Alternatives considered

- **An online font service:** the page would contact an outside server on every load, and without internet the message would fall back to another font anyway. It goes against running locally with no outside services.
- **A bundled font file in `static/`:** it would look the same on every computer, but the file would have to be downloaded from the internet. Its license would also need checking. The user chose not to do this.
