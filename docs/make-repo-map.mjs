// Generates ../Tools-map.excalidraw (run: node docs/make-repo-map.mjs from repo root,
// or node make-repo-map.mjs from docs/). Follows Repos/.claude/diagram-guidelines.md:
// ink text only, white chips on arrow midpoints with line visible on both sides,
// edge-to-edge arrows, one accent color, legend for line styles.
// docs/REPO_MAP.md is the source of truth. Preview: node docs/render-map-preview.mjs
// then npx sharp-cli -i docs/map-preview.svg -o docs/map-preview.png
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const OUT = join(dirname(fileURLToPath(import.meta.url)), "..", "Tools-map.excalidraw");

const INK = "#1c1913";
const INK_SOFT = "#55503f";
const INK_MUTED = "#6f6a59";
const ACCENT = "#17635a";

let n = 1000;
const el = (props) => ({
  id: "el" + n++,
  angle: 0,
  strokeColor: INK,
  backgroundColor: "transparent",
  fillStyle: "solid",
  strokeWidth: 1,
  strokeStyle: "solid",
  roughness: 1,
  opacity: 100,
  groupIds: [],
  frameId: null,
  roundness: { type: 3 },
  seed: n * 7919,
  version: 1,
  versionNonce: n * 104729,
  isDeleted: false,
  boundElements: null,
  updated: 1,
  link: null,
  locked: false,
  ...props,
});

const els = [];

const text = (x, y, str, size, color, family = 1) =>
  els.push(el({ type: "text", x, y, width: str.length * size * 0.62, height: size * 1.3, text: str, fontSize: size, fontFamily: family, textAlign: "left", verticalAlign: "top", baseline: size, containerId: null, originalText: str, lineHeight: 1.3, strokeColor: color, roundness: null }));

function zone(x, y, w, h, label, color) {
  els.push(el({ type: "rectangle", x, y, width: w, height: h, backgroundColor: color, strokeColor: "#8a8471", strokeStyle: "dashed", roughness: 0 }));
  text(x + 14, y + 10, label, 14, INK_MUTED, 3);
}

function box(x, y, w, h, title, sub, bg = "#ffffff", titleColor = INK, subColor = INK_SOFT, stroke = INK) {
  els.push(el({ type: "rectangle", x, y, width: w, height: h, backgroundColor: bg, strokeColor: stroke, roughness: 1 }));
  text(x + 12, y + 10, title, 15, titleColor);
  if (sub) {
    els.push(el({ type: "text", x: x + 12, y: y + 34, width: w - 24, height: h - 42, text: sub, fontSize: 12, fontFamily: 1, textAlign: "left", verticalAlign: "top", baseline: 12, containerId: null, originalText: sub, lineHeight: 1.3, strokeColor: subColor, roundness: null }));
  }
}

// Labels longer than 9 chars wrap to two lines at a space/hyphen so the chip
// never eats its arrow. Shared by chip() (drawing) and the arrow() guard.
function chipDims(label) {
  let lines = [label];
  if (label.length > 9) {
    const mid = Math.floor(label.length / 2);
    let best = -1;
    for (let i = 0; i < label.length; i++) {
      if (label[i] === " " || label[i] === "-") {
        if (best === -1 || Math.abs(i - mid) < Math.abs(best - mid)) best = i;
      }
    }
    if (best !== -1) {
      lines = [label.slice(0, best + (label[best] === "-" ? 1 : 0)).trim(), label.slice(best + 1).trim()];
    }
  }
  const wText = Math.max(...lines.map((l) => l.length)) * 7.2;
  return { lines, w: wText + 16, h: lines.length === 2 ? 34 : 20 };
}

// White chip with ink text centered on (cx, cy).
function chip(cx, cy, label) {
  const { lines, w, h } = chipDims(label);
  els.push(el({ type: "rectangle", x: cx - w / 2, y: cy - h / 2, width: w, height: h, backgroundColor: "#ffffff", strokeColor: "#c9c3b4", strokeWidth: 1, roughness: 0, roundness: { type: 3 } }));
  lines.forEach((ln, i) => {
    els.push(el({ type: "text", x: cx - (ln.length * 7.2) / 2, y: cy - h / 2 + 4 + i * 14, width: ln.length * 7.2, height: 14, text: ln, fontSize: 11, fontFamily: 3, textAlign: "left", verticalAlign: "top", baseline: 11, containerId: null, originalText: ln, lineHeight: 1.25, strokeColor: INK, roundness: null }));
  });
}

// Guard (diagram-guidelines rule 3): a chip must sit on a straight, axis-aligned
// segment and cover at most half of it, so line stays visible on both sides.
// Fails the whole generation loudly rather than emitting a jammed label.
function guardChip(pts, label, lx, ly) {
  const { w, h } = chipDims(label);
  let seg = null, best = Infinity;
  for (let i = 0; i < pts.length - 1; i++) {
    const [ax, ay] = pts[i], [bx, by] = pts[i + 1];
    const d = Math.hypot((ax + bx) / 2 - lx, (ay + by) / 2 - ly);
    if (d < best) { best = d; seg = [[ax, ay], [bx, by]]; }
  }
  const [[ax, ay], [bx, by]] = seg;
  const horizontal = ay === by, vertical = ax === bx;
  if (!horizontal && !vertical) {
    console.error(`FAIL: chip "${label}" sits on a diagonal segment (${ax},${ay})->(${bx},${by}); straighten the arrow under the chip.`);
    process.exit(1);
  }
  const segLen = horizontal ? Math.abs(bx - ax) : Math.abs(by - ay);
  const extent = horizontal ? w : h;
  if (extent > segLen / 2) {
    console.error(`FAIL: chip "${label}" (${Math.ceil(extent)}px) covers more than half of its ${segLen}px segment; lengthen the arrow to at least ${Math.ceil(extent * 2)}px (move the boxes apart).`);
    process.exit(1);
  }
}

// Arrow through absolute waypoints; chip at chipAt (defaults to path midpoint).
function arrow(pts, label, dashed = false, chipAt = null) {
  const [x0, y0] = pts[0];
  const rel = pts.map(([x, y]) => [x - x0, y - y0]);
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  els.push(el({ type: "arrow", x: x0, y: y0, width: Math.max(...xs) - Math.min(...xs), height: Math.max(...ys) - Math.min(...ys), points: rel, startBinding: null, endBinding: null, startArrowhead: null, endArrowhead: "arrow", strokeColor: ACCENT, strokeWidth: 2, strokeStyle: dashed ? "dashed" : "solid", roundness: { type: 2 } }));
  if (label) {
    const [lx, ly] = chipAt ?? [(pts[0][0] + pts[pts.length - 1][0]) / 2, (pts[0][1] + pts[pts.length - 1][1]) / 2];
    guardChip(pts, label, lx, ly);
    chip(lx, ly, label);
  }
}

// ── Title + legend ────────────────────────────────────────────────────────────
text(40, 20, "Tools: what each folder does", 24, INK);
text(40, 54, "verified 2026-07-16 · text twin that stays current: docs/REPO_MAP.md", 12, INK_MUTED, 3);
els.push(el({ type: "line", x: 800, y: 40, width: 40, height: 0, points: [[0, 0], [40, 0]], strokeColor: ACCENT, strokeWidth: 2, roundness: null }));
text(848, 32, "how a transcript is made", 12, INK_SOFT);
els.push(el({ type: "line", x: 1060, y: 40, width: 40, height: 0, points: [[0, 0], [40, 0]], strokeColor: ACCENT, strokeWidth: 2, strokeStyle: "dashed", roundness: null }));
text(1108, 32, "retired path", 12, INK_SOFT);

// ── Zones ─────────────────────────────────────────────────────────────────────
zone(40, 90, 260, 330, "INPUT", "#f4f0e8");
zone(390, 90, 300, 330, "WHISPER-TRANSCRIBE/", "#edf1f6");
zone(790, 90, 300, 330, "OUTPUT", "#eaf2f0");
zone(40, 460, 1330, 200, "REFERENCE (docs and the retired tool)", "#f2efe9");

// ── Boxes ─────────────────────────────────────────────────────────────────────
box(60, 170, 220, 110, "audio / video", "mp4, mp3, wav, m4a, mkv,\nwebm, avi, flac, ogg,\nor a whole folder");

box(415, 150, 250, 100, "transcribe.py", "wrapper around Whisper:\nauto-detects GPU, installs\nmissing deps, batches folders");
box(415, 330, 250, 80, "Whisper large-v3", "3 GB model, downloaded\nonce, runs fully local");

box(815, 150, 250, 110, "timestamped transcript", "one .md per input, saved\nnext to the original, with\n[0:00] paragraph stamps", "#17635a", "#ffffff", "#e4f0ee", "#17635a");

box(70, 505, 220, 120, "README.md", "front door: the table of\ntools and their doc links");
box(330, 505, 220, 120, "dictation/", "tombstone: custom tool\nretired, folder is now\na signpost");
box(760, 505, 240, 120, "Whisper Key Local", "external app by PinW:\nhotkey speech-to-text\nat the cursor, local");
box(1040, 505, 300, 120, "docs/ + this file", "REPO_MAP (text twin), MARKETING,\nmap generator; regenerate when\nstructure changes");

// ── Arrows (edge to edge; labeled segments straight, axis-aligned, 2x chip) ──
arrow([[280, 200], [415, 200]], "reads");                  // input -> transcribe.py (135px)
arrow([[540, 250], [540, 330]], "loads once");             // transcribe.py -> model (80px vertical)
arrow([[665, 190], [815, 190]], "writes .md");             // transcribe.py -> transcript (150px)
arrow([[550, 545], [760, 545]], "replaced by", true);      // dictation -> Whisper Key Local (210px, dashed)

const doc = {
  type: "excalidraw",
  version: 2,
  source: "tools-repo-map",
  elements: els,
  appState: { gridSize: null, viewBackgroundColor: "#ffffff" },
  files: {},
};
writeFileSync(OUT, JSON.stringify(doc, null, 1));
console.log("wrote", OUT, "with", els.length, "elements");
