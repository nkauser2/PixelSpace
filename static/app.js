// PixelSpace browser code.
// The browser draws strokes on screen as you move the mouse/finger/pen.
// When a stroke is finished it's sent to the Python server, which keeps the
// real artwork (and the undo/redo history). After every action the server
// sends back the full "state", and we redraw from it.

// ---------- page elements ----------
const paintCanvas = document.getElementById("paint-layer");
const paint = paintCanvas.getContext("2d");
const templateCanvas = document.getElementById("template-layer");
const templateCtx = templateCanvas.getContext("2d");
const selectionCanvas = document.getElementById("selection-layer");
const selectionCtx = selectionCanvas.getContext("2d");
const canvasWrap = document.getElementById("canvas-wrap");

const undoBtn = document.getElementById("undo-btn");
const redoBtn = document.getElementById("redo-btn");
const clearBtn = document.getElementById("clear-btn");
const toolButtons = document.querySelectorAll(".tool");
const sizeSlider = document.getElementById("size-slider");
const sizeValue = document.getElementById("size-value");
const swatches = document.querySelectorAll(".swatch");
const customColor = document.getElementById("custom-color");
const colorPreview = document.getElementById("color-preview");
const colorName = document.getElementById("color-name");
const recentColorsBox = document.getElementById("recent-colors");
const itemButtons = document.querySelectorAll(".item-btn");
const itemSizeSlider = document.getElementById("item-size");
const itemSizeValue = document.getElementById("item-size-value");
const flipHBtn = document.getElementById("flip-h-btn");
const flipVBtn = document.getElementById("flip-v-btn");
const rotateBtn = document.getElementById("rotate-btn");
const saveName = document.getElementById("save-name");
const saveBtn = document.getElementById("save-btn");
const openSelect = document.getElementById("open-select");
const openBtn = document.getElementById("open-btn");
const renameName = document.getElementById("rename-name");
const renameBtn = document.getElementById("rename-btn");
const downloadBtn = document.getElementById("download-btn");
const galleryBtn = document.getElementById("gallery-btn");
const gallery = document.getElementById("gallery");
const galleryGrid = document.getElementById("gallery-grid");
const galleryEmpty = document.getElementById("gallery-empty");
const galleryClose = document.getElementById("gallery-close");
const toast = document.getElementById("toast");

// ---------- what the user has chosen ----------
let tool = "brush";
let color = customColor.value;
let size = Number(sizeSlider.value);
let chosenItem = null;     // the shape, letter or number the Place tool puts down (R7)
let itemSize = Number(itemSizeSlider.value);

// ---------- the artwork ----------
let strokes = [];          // strokes and placed items the server has confirmed
let pendingStrokes = [];   // finished strokes still on their way to the server
let currentStroke = null;  // the stroke being drawn right now
let templateId = null;     // only artwork saved before Round 3 can have one
const templateCache = {};
let shapeOutlines = {};    // shape id -> outline points, from /api/items
let selectedIndex = null;  // which placed item is selected (R7, R11), or null

// ---------- talking to the server ----------
// Requests are sent one at a time, in order, so a quick "draw then undo"
// always happens in the right sequence.
let requestQueue = Promise.resolve();

function api(method, url, data) {
  const run = async () => {
    const options = { method, headers: { "Content-Type": "application/json" } };
    if (data !== undefined) options.body = JSON.stringify(data);
    const response = await fetch(url, options);
    const json = await response.json().catch(() => ({}));
    return { ok: response.ok, status: response.status, data: json };
  };
  const result = requestQueue.then(run);
  requestQueue = result.catch(() => {});
  return result;
}

function applyState(state) {
  strokes = state.strokes;
  undoBtn.disabled = !state.can_undo;
  redoBtn.disabled = !state.can_redo;
  // Drop the selection if that item isn't there any more.
  if (selectedIndex !== null && !(strokes[selectedIndex] && strokes[selectedIndex].tool === "item")) {
    selectedIndex = null;
  }
  render();
  showTemplate(state.template);
}

async function reloadState() {
  const res = await api("GET", "/api/state");
  if (res.ok) applyState(res.data);
}

// ---------- drawing ----------
function setUpPen(ctx, stroke) {
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.lineWidth = stroke.size;
  if (stroke.tool === "eraser") {
    // "destination-out" removes paint instead of adding it.
    ctx.globalCompositeOperation = "destination-out";
    ctx.strokeStyle = ctx.fillStyle = "#000";
  } else {
    ctx.globalCompositeOperation = "source-over";
    ctx.strokeStyle = ctx.fillStyle = stroke.color;
  }
}

// A placed shape, letter or number (R7), filled with its color.
// The steps match item_point_on_canvas in canvas_model.py: move to the
// center, turn clockwise, then mirror (canvas transforms apply last-first).
function drawItem(ctx, item) {
  ctx.save();
  ctx.globalCompositeOperation = "source-over";
  ctx.fillStyle = item.color;
  ctx.translate(item.x, item.y);
  ctx.rotate((item.rotation * Math.PI) / 180);
  ctx.scale(item.flip_x ? -1 : 1, item.flip_y ? -1 : 1);
  const outline = shapeOutlines[item.item];
  if (outline) {
    ctx.beginPath();
    ctx.moveTo(outline[0][0] * item.size, outline[0][1] * item.size);
    for (const [x, y] of outline.slice(1)) ctx.lineTo(x * item.size, y * item.size);
    ctx.closePath();
    ctx.fill();
  } else {
    // A letter or number: big bold text, centered on the item's middle.
    ctx.font = `bold ${item.size}px system-ui, "Segoe UI", Roboto, sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "alphabetic";
    const m = ctx.measureText(item.item);
    const middle = (m.actualBoundingBoxAscent - m.actualBoundingBoxDescent) / 2;
    ctx.fillText(item.item, 0, middle);
  }
  ctx.restore();
}

function drawStroke(ctx, stroke) {
  if (stroke.tool === "item") {
    drawItem(ctx, stroke);
    return;
  }
  const pts = stroke.points;
  ctx.save();
  setUpPen(ctx, stroke);
  ctx.beginPath();
  if (pts.length === 1) {
    // A single click makes a dot.
    ctx.arc(pts[0][0], pts[0][1], stroke.size / 2, 0, Math.PI * 2);
    ctx.fill();
  } else {
    ctx.moveTo(pts[0][0], pts[0][1]);
    for (const [x, y] of pts.slice(1)) ctx.lineTo(x, y);
    ctx.stroke();
  }
  ctx.restore();
}

function drawSegment(stroke, from, to) {
  paint.save();
  setUpPen(paint, stroke);
  paint.beginPath();
  paint.moveTo(from[0], from[1]);
  paint.lineTo(to[0], to[1]);
  paint.stroke();
  paint.restore();
}

function render() {
  paint.clearRect(0, 0, paintCanvas.width, paintCanvas.height);
  for (const stroke of strokes) drawStroke(paint, stroke);
  for (const stroke of pendingStrokes) drawStroke(paint, stroke);
  if (currentStroke) drawStroke(paint, currentStroke);
  drawSelection();
}

// ---------- the selected item (R7, R11) ----------
// A dashed box shows which item is selected. The flip and rotate buttons
// only work when something is selected.
function drawSelection() {
  selectionCtx.clearRect(0, 0, selectionCanvas.width, selectionCanvas.height);
  const item = selectedIndex === null ? null : strokes[selectedIndex];
  const hasItem = Boolean(item && item.tool === "item");
  flipHBtn.disabled = flipVBtn.disabled = rotateBtn.disabled = !hasItem;
  if (!hasItem) return;
  const half = item.size / 2 + 4;
  selectionCtx.save();
  selectionCtx.setLineDash([8, 6]);
  selectionCtx.lineWidth = 2;
  selectionCtx.strokeStyle = "#7b4fd6";
  selectionCtx.strokeRect(item.x - half, item.y - half, half * 2, half * 2);
  selectionCtx.restore();
}

function setSelected(index) {
  selectedIndex = index;
  drawSelection();
}

// Convert a mouse/touch position into canvas coordinates
// (the canvas may be shown smaller or bigger than 800 x 600).
function toCanvasPoint(event) {
  const rect = paintCanvas.getBoundingClientRect();
  const x = ((event.clientX - rect.left) * paintCanvas.width) / rect.width;
  const y = ((event.clientY - rect.top) * paintCanvas.height) / rect.height;
  return [Math.round(x * 10) / 10, Math.round(y * 10) / 10];
}

// Place tool (R7): put the chosen item down with its center at the click.
async function placeItemAt(point) {
  if (!chosenItem) {
    showToast("Choose a shape, letter or number first.", true);
    return;
  }
  const res = await api("POST", "/api/item", { item: chosenItem, color, size: itemSize, x: point[0], y: point[1] });
  if (res.ok) {
    applyState(res.data);
    setSelected(res.data.selected); // the new item is selected, ready to flip or rotate
  } else {
    showToast(res.data.error || "That item couldn't be placed.", true);
  }
}

// Select tool (R7, R11): select the top item under the click, or nothing.
async function selectAt(point) {
  const res = await api("POST", "/api/item-at", { x: point[0], y: point[1] });
  if (res.ok) setSelected(res.data.index);
}

canvasWrap.addEventListener("pointerdown", (event) => {
  if (event.button !== 0) return; // left button / finger / pen only
  if (tool === "place") {
    placeItemAt(toCanvasPoint(event));
    return;
  }
  if (tool === "select") {
    selectAt(toCanvasPoint(event));
    return;
  }
  canvasWrap.setPointerCapture(event.pointerId);
  currentStroke = {
    tool,
    color: tool === "eraser" ? null : color,
    size,
    points: [toCanvasPoint(event)],
  };
  drawStroke(paint, currentStroke);
});

canvasWrap.addEventListener("pointermove", (event) => {
  if (!currentStroke) return;
  // Coalesced events give smoother lines on fast movements.
  const events = event.getCoalescedEvents ? event.getCoalescedEvents() : [event];
  for (const e of events.length ? events : [event]) {
    const point = toCanvasPoint(e);
    const last = currentStroke.points[currentStroke.points.length - 1];
    if (Math.hypot(point[0] - last[0], point[1] - last[1]) < 1) continue;
    currentStroke.points.push(point);
    drawSegment(currentStroke, last, point);
  }
});

async function finishStroke() {
  if (!currentStroke) return;
  const stroke = currentStroke;
  currentStroke = null;
  pendingStrokes.push(stroke);
  const res = await api("POST", "/api/stroke", stroke);
  pendingStrokes = pendingStrokes.filter((s) => s !== stroke);
  if (res.ok) {
    applyState(res.data);
  } else {
    showToast(res.data.error || "That stroke couldn't be added.", true);
    reloadState();
  }
}

canvasWrap.addEventListener("pointerup", finishStroke);
canvasWrap.addEventListener("pointercancel", finishStroke);

// ---------- template outlines (only in artwork saved before Round 3) ----------
// Templates were replaced by placeable items in Round 3 (R7), but old saves
// that use one still show its outline on top of the paint.
function drawShape(ctx, shape) {
  ctx.beginPath();
  if (shape.type === "circle") {
    ctx.arc(shape.cx, shape.cy, shape.r, 0, Math.PI * 2);
  } else if (shape.type === "ellipse") {
    ctx.ellipse(shape.cx, shape.cy, shape.rx, shape.ry, (shape.rotation * Math.PI) / 180, 0, Math.PI * 2);
  } else if (shape.type === "rect") {
    ctx.rect(shape.x, shape.y, shape.w, shape.h);
  } else if (shape.type === "line" || shape.type === "polygon") {
    ctx.moveTo(shape.points[0][0], shape.points[0][1]);
    for (const [x, y] of shape.points.slice(1)) ctx.lineTo(x, y);
    if (shape.type === "polygon") ctx.closePath();
  }
  ctx.stroke();
}

// Fetch a template's outline once, then keep it. Returns null if it's unknown.
async function getTemplate(id) {
  if (!templateCache[id]) {
    const res = await fetch(`/api/templates/${encodeURIComponent(id)}`);
    if (!res.ok) return null;
    templateCache[id] = await res.json();
  }
  return templateCache[id];
}

// Draw a template's outline. Used on the canvas and in gallery previews (R15).
function drawTemplate(ctx, template) {
  ctx.save();
  ctx.strokeStyle = "#2b2d3a";
  ctx.lineWidth = 4;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  for (const shape of template.shapes) drawShape(ctx, shape);
  ctx.restore();
}

async function showTemplate(id) {
  templateId = id;
  templateCtx.clearRect(0, 0, templateCanvas.width, templateCanvas.height);
  if (!id) return;

  const template = await getTemplate(id);
  if (!template || templateId !== id) return; // unknown, or the user picked something else meanwhile

  templateCtx.clearRect(0, 0, templateCanvas.width, templateCanvas.height);
  drawTemplate(templateCtx, template);
}

// ---------- tools, size and colors ----------
function setTool(newTool) {
  tool = newTool;
  toolButtons.forEach((b) => b.classList.toggle("active", b.dataset.tool === tool));
  canvasWrap.classList.toggle("placing", tool === "place");
  canvasWrap.classList.toggle("selecting", tool === "select");
  // Painting or erasing means you're done with the selected item.
  if (tool === "brush" || tool === "eraser") setSelected(null);
}

// Choosing an item in the grid gets the Place tool ready to put it down.
function chooseItem(itemId) {
  chosenItem = itemId;
  itemButtons.forEach((b) => b.classList.toggle("active", b.dataset.item === itemId));
  setTool("place");
}

function setColor(hex) {
  color = hex.toLowerCase();
  colorPreview.style.background = color;
  colorName.textContent = color;
  customColor.value = color;
  swatches.forEach((s) => s.classList.toggle("active", s.dataset.color === color));
  recentColorsBox.querySelectorAll(".swatch").forEach((s) => s.classList.toggle("active", s.dataset.color === color));
  if (tool === "eraser") setTool("brush"); // picking a color means you want to paint
}

// ---------- recent colors (R9) ----------
// The server remembers the 5 most recently picked colors (newest first,
// each only once). We just draw whatever list it sends back.
function showRecentColors(colors) {
  recentColorsBox.innerHTML = "";
  if (colors.length === 0) {
    recentColorsBox.innerHTML = '<span class="recent-empty">Colors you pick will show up here.</span>';
    return;
  }
  for (const hex of colors) {
    const button = document.createElement("button");
    button.className = "swatch" + (hex === color ? " active" : "");
    button.dataset.color = hex;
    button.title = `Use ${hex} again`;
    button.style.background = hex;
    button.addEventListener("click", () => pickColor(hex));
    recentColorsBox.appendChild(button);
  }
}

// "Picking" a color = choosing it on purpose: a palette swatch, a recent
// color, or closing the custom picker. It becomes the current color AND
// goes to the front of the recent list.
// If an item is selected, it is re-colored too (R7).
async function pickColor(hex) {
  setColor(hex);
  if (selectedIndex !== null) {
    const recolored = await api("POST", "/api/item/recolor", { index: selectedIndex, color: hex });
    if (recolored.ok) applyState(recolored.data);
    else showToast(recolored.data.error || "Couldn't re-color that item.", true);
  }
  const res = await api("POST", "/api/recent-colors", { color: hex });
  if (res.ok) showRecentColors(res.data);
}

async function loadRecentColors() {
  const res = await api("GET", "/api/recent-colors");
  if (res.ok) showRecentColors(res.data);
}

toolButtons.forEach((b) => b.addEventListener("click", () => setTool(b.dataset.tool)));
swatches.forEach((s) => s.addEventListener("click", () => pickColor(s.dataset.color)));
// While dragging inside the custom picker, the color updates live ("input")
// but only the final choice, when the picker closes ("change"), counts as picked.
customColor.addEventListener("input", () => setColor(customColor.value));
customColor.addEventListener("change", () => pickColor(customColor.value));
sizeSlider.addEventListener("input", () => {
  size = Number(sizeSlider.value);
  sizeValue.textContent = size;
});

// ---------- shapes, letters and numbers (R7) ----------
itemButtons.forEach((b) => b.addEventListener("click", () => chooseItem(b.dataset.item)));
itemSizeSlider.addEventListener("input", () => {
  itemSize = Number(itemSizeSlider.value);
  itemSizeValue.textContent = itemSize;
});

async function loadShapeOutlines() {
  const res = await api("GET", "/api/items");
  if (!res.ok) return;
  for (const item of res.data) {
    if (item.points) shapeOutlines[item.id] = item.points;
  }
  render(); // items may have been drawn before their outlines arrived
}

// ---------- flip and rotate the selected item (R11) ----------
async function changeSelected(url, extra = {}) {
  if (selectedIndex === null) return;
  const res = await api("POST", url, { index: selectedIndex, ...extra });
  if (res.ok) applyState(res.data);
  else showToast(res.data.error || "Couldn't change that item.", true);
}

flipHBtn.addEventListener("click", () => changeSelected("/api/item/flip", { direction: "horizontal" }));
flipVBtn.addEventListener("click", () => changeSelected("/api/item/flip", { direction: "vertical" }));
rotateBtn.addEventListener("click", () => changeSelected("/api/item/rotate"));

// ---------- undo, redo, clear ----------
// Undo, redo, clear and opening artwork all clear the selection.
async function undo() {
  selectedIndex = null;
  const res = await api("POST", "/api/undo");
  if (res.ok) applyState(res.data);
}

async function redo() {
  selectedIndex = null;
  const res = await api("POST", "/api/redo");
  if (res.ok) applyState(res.data);
}

undoBtn.addEventListener("click", undo);
redoBtn.addEventListener("click", redo);

clearBtn.addEventListener("click", async () => {
  if (strokes.length === 0 && !templateId) {
    showToast("The canvas is already empty.");
    return;
  }
  if (!confirm("Clear the whole canvas? (You can still undo this.)")) return;
  selectedIndex = null;
  const res = await api("POST", "/api/clear");
  if (res.ok) applyState(res.data);
});

// Keyboard shortcuts (ignored while typing in a text box).
document.addEventListener("keydown", (event) => {
  // While the gallery (R15) is open, Escape closes it and the drawing
  // shortcuts are off, so nothing changes on the canvas hidden behind it.
  if (!gallery.hidden) {
    if (event.key === "Escape") closeGallery();
    return;
  }
  if (event.target.matches("input[type=text], select")) return;
  const key = event.key.toLowerCase();
  if ((event.ctrlKey || event.metaKey) && key === "z" && !event.shiftKey) {
    event.preventDefault();
    undo();
  } else if ((event.ctrlKey || event.metaKey) && (key === "y" || (key === "z" && event.shiftKey))) {
    event.preventDefault();
    redo();
  } else if (!event.ctrlKey && !event.metaKey && key === "b") {
    setTool("brush");
  } else if (!event.ctrlKey && !event.metaKey && key === "e") {
    setTool("eraser");
  } else if (!event.ctrlKey && !event.metaKey && key === "p") {
    setTool("place");
  } else if (!event.ctrlKey && !event.metaKey && key === "s") {
    setTool("select");
  }
});

// ---------- saving and opening ----------
async function refreshSavedList(selectName) {
  const res = await api("GET", "/api/saves");
  if (!res.ok) return;
  openSelect.innerHTML = '<option value="">— Saved artwork —</option>';
  for (const name of res.data) {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    openSelect.appendChild(option);
  }
  if (selectName) openSelect.value = selectName;
}

saveBtn.addEventListener("click", async () => {
  const name = saveName.value.trim();
  if (!name) {
    showToast("Type a name for your artwork first.", true);
    saveName.focus();
    return;
  }
  let res = await api("POST", "/api/save", { name });
  if (res.status === 409) {
    // Never replace saved artwork without asking.
    if (!confirm(`${res.data.error} Do you want to replace it?`)) return;
    res = await api("POST", "/api/save", { name, overwrite: true });
  }
  if (res.ok) {
    saveName.value = res.data.saved;
    showToast(`Saved as "${res.data.saved}" ✓`);
    refreshSavedList(res.data.saved);
  } else {
    showToast(res.data.error || "Couldn't save your artwork.", true);
  }
});

// Open a saved artwork on the canvas. Used by the Open button and by the
// gallery (R15). Asks first if that would replace a drawing. Returns true if
// the artwork was opened.
async function openArtwork(name) {
  const hasWork = strokes.length > 0 || templateId;
  if (hasWork && !confirm(`Open "${name}"? Anything unsaved on the current canvas will be replaced.`)) return false;
  const res = await api("POST", "/api/load", { name });
  if (res.ok) {
    selectedIndex = null;
    applyState(res.data);
    saveName.value = name;
    openSelect.value = name; // keep the "Saved artwork" list (and Rename) in step
    showToast(`Opened "${name}"`);
    return true;
  }
  showToast(res.data.error || "Couldn't open that artwork.", true);
  return false;
}

openBtn.addEventListener("click", () => {
  const name = openSelect.value;
  if (!name) {
    showToast("Choose a saved artwork to open.", true);
    return;
  }
  openArtwork(name);
});

// Rename (R10): rename the artwork chosen in the "Saved artwork" list.
renameBtn.addEventListener("click", async () => {
  const oldName = openSelect.value;
  const newName = renameName.value.trim();
  if (!oldName) {
    showToast("Choose a saved artwork to rename.", true);
    return;
  }
  if (!newName) {
    showToast("Type the new name first.", true);
    renameName.focus();
    return;
  }
  let res = await api("POST", "/api/rename", { old_name: oldName, new_name: newName });
  if (res.status === 409) {
    // Never replace another saved artwork without asking.
    const ok = confirm(`${res.data.error} Renaming "${oldName}" will replace it, and its old drawing will be lost. Replace it?`);
    if (!ok) return;
    res = await api("POST", "/api/rename", { old_name: oldName, new_name: newName, overwrite: true });
  }
  if (res.ok) {
    const renamed = res.data.renamed;
    // If the renamed artwork is the one that's open, keep the name box in step.
    if (saveName.value.trim() === oldName) saveName.value = renamed;
    renameName.value = "";
    showToast(`Renamed "${oldName}" to "${renamed}" ✓`);
    refreshSavedList(renamed);
  } else {
    showToast(res.data.error || "Couldn't rename that artwork.", true);
  }
});

downloadBtn.addEventListener("click", () => {
  // Combine a white background, the paint and the template into one image.
  const out = document.createElement("canvas");
  out.width = paintCanvas.width;
  out.height = paintCanvas.height;
  const ctx = out.getContext("2d");
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, out.width, out.height);
  ctx.drawImage(paintCanvas, 0, 0);
  ctx.drawImage(templateCanvas, 0, 0);
  const link = document.createElement("a");
  link.download = `${saveName.value.trim() || "pixelspace"}.png`;
  link.href = out.toDataURL("image/png");
  link.click();
});

// ---------- the gallery of saved artwork (R15) ----------
// A pop-up with a small preview of every saved artwork, in the order the
// server sends them: the most recently saved first. The CSS puts five in a row.
const PREVIEW_WIDTH = 200; // pixels inside each preview; the CSS sets its size on screen

// Draw a saved artwork small, the same way the canvas shows it: paint and
// placed items, then (for artwork saved before Round 3) the template outline
// on top. Only the artwork is drawn, on the preview's white CSS background.
async function drawPreview(preview, entry) {
  const ctx = preview.getContext("2d");
  const scale = preview.width / paintCanvas.width;
  ctx.save();
  ctx.scale(scale, scale);
  for (const stroke of entry.strokes) drawStroke(ctx, stroke);
  ctx.restore();
  if (!entry.template) return;
  const template = await getTemplate(entry.template);
  if (!template) return;
  ctx.save();
  ctx.scale(scale, scale);
  drawTemplate(ctx, template);
  ctx.restore();
}

// One card in the gallery: the preview (or a note if the file is damaged)
// and the artwork's name. Clicking it opens the artwork.
function makeGalleryCard(entry) {
  const card = document.createElement("button");
  card.className = "gallery-item";
  if (entry.damaged) {
    card.disabled = true;
    card.title = `"${entry.name}" is damaged and can't be opened`;
    const note = document.createElement("span");
    note.className = "gallery-broken";
    note.textContent = "Can't be shown";
    card.appendChild(note);
  } else {
    card.title = `Open "${entry.name}"`;
    const preview = document.createElement("canvas");
    preview.className = "gallery-preview";
    preview.width = PREVIEW_WIDTH;
    preview.height = Math.round((PREVIEW_WIDTH * paintCanvas.height) / paintCanvas.width);
    card.appendChild(preview);
    drawPreview(preview, entry);
    card.addEventListener("click", () => openFromGallery(entry.name));
  }
  const label = document.createElement("span");
  label.className = "gallery-name";
  label.textContent = entry.name;
  card.appendChild(label);
  return card;
}

async function openGallery() {
  const res = await api("GET", "/api/gallery");
  if (!res.ok) {
    showToast("Couldn't load the gallery.", true);
    return;
  }
  await outlinesReady; // placed shapes need their outlines to be drawn
  galleryGrid.innerHTML = "";
  galleryEmpty.hidden = res.data.length > 0;
  for (const entry of res.data) galleryGrid.appendChild(makeGalleryCard(entry));
  gallery.hidden = false;
  galleryClose.focus();
}

function closeGallery() {
  gallery.hidden = true;
  galleryBtn.focus();
}

// The gallery closes once the artwork is open. If the user says no to
// replacing their drawing, it stays open so they can choose another.
async function openFromGallery(name) {
  if (await openArtwork(name)) closeGallery();
}

galleryBtn.addEventListener("click", openGallery);
galleryClose.addEventListener("click", closeGallery);
// A click on the dark area around the pop-up closes it too.
gallery.addEventListener("click", (event) => {
  if (event.target === gallery) closeGallery();
});

// ---------- little pop-up messages ----------
let toastTimer;
function showToast(message, isError = false) {
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 2500);
}

// ---------- start ----------
const outlinesReady = loadShapeOutlines();
reloadState();
refreshSavedList();
loadRecentColors();
