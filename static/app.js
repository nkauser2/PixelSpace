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
const templateSelect = document.getElementById("template-select");
const saveName = document.getElementById("save-name");
const saveBtn = document.getElementById("save-btn");
const openSelect = document.getElementById("open-select");
const openBtn = document.getElementById("open-btn");
const downloadBtn = document.getElementById("download-btn");
const toast = document.getElementById("toast");

// ---------- what the user has chosen ----------
let tool = "brush";
let color = customColor.value;
let size = Number(sizeSlider.value);

// ---------- the artwork ----------
let strokes = [];          // strokes the server has confirmed
let pendingStrokes = [];   // finished strokes still on their way to the server
let currentStroke = null;  // the stroke being drawn right now
let templateId = null;
const templateCache = {};

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

function drawStroke(ctx, stroke) {
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
}

// Convert a mouse/touch position into canvas coordinates
// (the canvas may be shown smaller or bigger than 800 x 600).
function toCanvasPoint(event) {
  const rect = paintCanvas.getBoundingClientRect();
  const x = ((event.clientX - rect.left) * paintCanvas.width) / rect.width;
  const y = ((event.clientY - rect.top) * paintCanvas.height) / rect.height;
  return [Math.round(x * 10) / 10, Math.round(y * 10) / 10];
}

canvasWrap.addEventListener("pointerdown", (event) => {
  if (event.button !== 0) return; // left button / finger / pen only
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

// ---------- coloring templates ----------
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

async function showTemplate(id) {
  templateId = id;
  templateSelect.value = id || "";
  templateCtx.clearRect(0, 0, templateCanvas.width, templateCanvas.height);
  if (!id) return;

  if (!templateCache[id]) {
    const res = await fetch(`/api/templates/${encodeURIComponent(id)}`);
    if (!res.ok) return;
    templateCache[id] = await res.json();
  }
  if (templateId !== id) return; // the user picked something else meanwhile

  templateCtx.clearRect(0, 0, templateCanvas.width, templateCanvas.height);
  templateCtx.strokeStyle = "#2b2d3a";
  templateCtx.lineWidth = 4;
  templateCtx.lineCap = "round";
  templateCtx.lineJoin = "round";
  for (const shape of templateCache[id].shapes) drawShape(templateCtx, shape);
}

templateSelect.addEventListener("change", async () => {
  const res = await api("POST", "/api/template", { id: templateSelect.value || null });
  if (res.ok) applyState(res.data);
  else {
    showToast(res.data.error || "Couldn't load that template.", true);
    templateSelect.value = templateId || "";
  }
});

// ---------- tools, size and colors ----------
function setTool(newTool) {
  tool = newTool;
  toolButtons.forEach((b) => b.classList.toggle("active", b.dataset.tool === tool));
}

function setColor(hex) {
  color = hex.toLowerCase();
  colorPreview.style.background = color;
  colorName.textContent = color;
  customColor.value = color;
  swatches.forEach((s) => s.classList.toggle("active", s.dataset.color === color));
  recentColorsBox.querySelectorAll(".swatch").forEach((s) => s.classList.toggle("active", s.dataset.color === color));
  setTool("brush"); // picking a color means you want to paint
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
async function pickColor(hex) {
  setColor(hex);
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

// ---------- undo, redo, clear ----------
async function undo() {
  const res = await api("POST", "/api/undo");
  if (res.ok) applyState(res.data);
}

async function redo() {
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
  const res = await api("POST", "/api/clear");
  if (res.ok) applyState(res.data);
});

// Keyboard shortcuts (ignored while typing in a text box).
document.addEventListener("keydown", (event) => {
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

openBtn.addEventListener("click", async () => {
  const name = openSelect.value;
  if (!name) {
    showToast("Choose a saved artwork to open.", true);
    return;
  }
  const hasWork = strokes.length > 0 || templateId;
  if (hasWork && !confirm(`Open "${name}"? Anything unsaved on the current canvas will be replaced.`)) return;
  const res = await api("POST", "/api/load", { name });
  if (res.ok) {
    applyState(res.data);
    saveName.value = name;
    showToast(`Opened "${name}"`);
  } else {
    showToast(res.data.error || "Couldn't open that artwork.", true);
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
reloadState();
refreshSavedList();
loadRecentColors();
