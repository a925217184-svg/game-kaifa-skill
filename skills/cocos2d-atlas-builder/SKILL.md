---
name: cocos2d-atlas-builder
description: Build square transparent sprite atlases (N×N grid) from an ordered folder of PNG frames and emit standard Cocos2d .plist files (format=2, RGBA8888, premultiplyAlpha) that load correctly in Cocos Creator / cocos2d-x. Use when packing keyed/transparent animation frames into a sprite sheet plus a usable plist, comparing 8×8 vs 4×4 atlases for size, or when a generated plist fails to parse in Cocos (e.g. "reading 'slice'/'indexes'" errors or a non-standard plist).
agent_created: true
---

# Cocos2d Atlas Builder

## Overview

Pack a folder of **ordered, already-keyed/transparent PNG frames** into a square
sprite atlas and generate a **standard Cocos2d `.plist`** that Cocos Creator /
cocos2d-x imports without errors. The plist format is reverse-engineered from
Free Texture Packer's "Cocos2d" export template (see
`references/cocos2d_plist_spec.md`) and self-validated with `plistlib`.

This skill only handles **atlas packing + plist generation**. The upstream
keying / green-screen removal that produces transparent frames is out of scope;
feed clean transparent frames in.

## When to use

- Packing animation frames (cats, characters, VFX) into a single transparent sheet.
- Needing a `.plist` alongside the PNG so Cocos can slice frames by name.
- Comparing atlas sizes: e.g. 8×8 = 64 frames (2048², larger) vs 4×4 = 16 frames (1024², smaller).
- A previously generated plist fails to load in Cocos (format/spec mismatch).

## Workflow

### Step 1 — Build the atlas

Run `scripts/build_atlas.py` with the folder of ordered PNG frames:

```bash
python scripts/build_atlas.py \
  --src  /path/to/ordered_frames \
  --out  /path/to/output \
  --name cat_pink \
  --grid 4 \            # 4 -> 4×4 = 16 frames; use 8 -> 8×8 = 64
  --cell 256 \          # each frame resized to 256×256
  --defringe-green      # optional: knock out leftover green-screen fringe
  --key-black           # optional: make near-black background transparent (border flood fill)
  --content-max 195 \   # optional: fit content so longest side == 195 px, centered in 256 cell
  --content-height 195 \ # optional: fit content so height == 195 px, centered in 256 cell
  --no-frames           # optional: skip the frames/ subfolder (atlas + .atlas only)
  --no-preview          # optional: skip the preview_<name>.png grid sheet
```

Outputs in `--out`:
- `cat_pink.png` — square transparent atlas (grid×cell px).
- `cat_pink.atlas` — libGDX-style frame map (consumed by Step 2).
- `frames/` — individual resized frames (use for the preview GIF). Only when
  `--no-frames` is NOT given.
- `preview_cat_pink.png` — grid preview with frame indices. Only when
  `--no-preview` is NOT given.

Behavior notes:
- Frame count is forced to `grid×grid`. First source frame = atlas frame 0, last
  source frame = atlas last frame (forced unless `--no-keep-ends`). Middle frames
  are uniformly sampled in playback order so the loop is smooth.
- When the source has **fewer** frames than the target grid (e.g. 61 source frames
  for an 8×8 = 64 atlas), frames are interpolated with duplicates allowed so the
  atlas still emits exactly `grid×grid` frames; first/last are still forced to the
  true first/last source keyframes.
- Every frame is LANCZOS-resized to `--cell`, preserving relative position → no
  jump between frames.
- `--key-black` makes a near-black (RGB `< 40`) background transparent via a
  border-connected flood fill, so genuinely dark parts of the subject stay opaque.
  Use it for sprites shot on a solid black backdrop.
- `--content-max N` crops each frame to its alpha bounding box, scales it so the
  longest side equals `N` px, and pastes it centered inside the `cell×cell` slot.
  Use it when sprites from different sources end up different visual sizes in the
  atlas (e.g. one set was drawn closer to the camera). Pick `N` by measuring the
  content bounding boxes of the reference atlas you want to match.
- `--content-height N` crops each frame to its alpha bounding box, scales it so
  the **height** equals `N` px, and pastes it centered inside the `cell×cell` slot.
  Use it when frames inside the same atlas vary in visual height (e.g. sleep
  pose vs standing pose) and you want them to look the same size. `--content-max`
  and `--content-height` are mutually exclusive.
- `--src` and `--out` may be the same folder. A pre-existing atlas PNG/atlas with
  the same `--name` is ignored on re-runs (re-run safe).
- Atlas background is fully transparent (RGBA alpha = 0).

### Step 2 — Generate the Cocos2d plist

Run `scripts/gen_plist.py` on the `.atlas` from Step 1:

```bash
python scripts/gen_plist.py \
  --atlas /path/to/output/cat_pink.atlas \
  --out   /path/to/output/cat_pink.plist
```

The script prints `frames=… format=2 RGBA8888 -> OK` (or `PARSE-FAIL` if
malformed). The plist strictly follows the Free Texture Packer "Cocos2d" template:
DOCTYPE `-//Apple Computer//DTD PLIST 1.0//EN`, `format=2`,
`pixelFormat=RGBA8888`, `premultiplyAlpha=<false/>`, 2-space indent, and **no
spaces inside rect strings** (`{{0,0},{256,256}}`).

### Step 3 — (optional) Playback GIF for visual check

```bash
python scripts/make_preview_gif.py \
  --frames /path/to/output/frames \
  --out    /path/to/output/playback.gif \
  --fps 12 --resize 256
```

Use the GIF to verify the animation loops smoothly and the first/last frames are
preserved before shipping into Cocos.

## Workflow B — TexturePacker (recommended when available)

If **TexturePacker (CodeAndWeb)** is installed and licensed on the machine, prefer
this over the pure-Python path. It emits a **standard cocos2d plist** (format=3,
RGBA8888, `premultiplyAlpha=false`) that Cocos Creator imports natively, and its
`--extrude` / `--shape-padding` / `--border-padding` flags are the industry-standard
fix for *"single-frame edges come out dirty / cut into the neighbor frame"* — exactly
the edge-bleed problem the manual path struggles with.

### Why it beats the manual path
- Padding + extrude are handled by the tool, not by hand-rolled rect math.
- The `format=3` plist with `textureRect` keys is generated correctly every time
  (the manual path's `gen_plist.py` makes `format=2` — both import fine, but TP's
  is what real tooling produces).
- Adjacent frames get a real transparent gutter, so even with Cocos mipmaps ON the
  shrunken sprite never samples a neighbor's pixels.

### Step B1 — Normalize each frame (Python side)
TexturePacker packs whatever you hand it. To get a clean, consistent N×N grid you
must normalize first:
- crop each frame to its **alpha bounding box** (alpha > ~30),
- **uniform-scale** so the longest content side == `content-max` (e.g. 224),
- **center horizontally + align feet to the bottom** inside a fixed `cell-prep`
  canvas (e.g. 240), so every frame is the same size and same pose position.

Do NOT skip this — feeding raw 960×960 frames with off-center subjects makes the
character drift between cells.

### Step B1b — `--keep-ratio` mode (eliminate per-frame jumping)

When every source frame is already the **same size** (e.g. a rendered sequence all
960×960) and you want the character to sit perfectly still between frames (no
scale/bob/jump), pass `--keep-ratio --pad 4` instead of `--content-max`:

```bash
python scripts/build_with_texturepacker.py \
  --src /path/to/ordered_frames --out /path/to/out --name passerby_1_happy \
  --grid 4 --sheet 1024 --cell-prep 240 --keep-ratio --pad 4 --tp "<tp.exe>"
```

What it does differently from the normalize path:
- **No alpha-bbox crop** — every pixel of the original frame is kept (only uniformly
  scaled), so you never lose transparent margin or accidentally re-frame the subject.
- **One global scale factor** for the whole set: `scale = (cell-prep − 2·pad) / max_dim`,
  where `max_dim` is the largest frame dimension across the picked frames. The SAME
  scale is applied to every frame → relative sizes and positions are locked → the
  loop plays without any artificial scale/position jump.
- Each frame is centered in its `cell-prep` canvas; since the source sequence is
  consistently framed, the subject stays put across the loop.

Use this when the *jumping* comes from per-frame re-normalization (content bbox
drifts frame to frame). If instead frames come from different sources at different
visual sizes, use `--content-max` (B1) to equalize them.

### Step B2 — Pack with TexturePacker CLI
Use `scripts/build_with_texturepacker.py` (wraps the steps below):

```bash
python scripts/build_with_texturepacker.py \
  --src  /path/to/ordered_frames \
  --out  /path/to/out \
  --name passerby_1_happy \
  --grid 4 --sheet 1024 \
  --content-max 224 --cell-prep 240 \
  --tp "C:/Program Files/CodeAndWeb/TexturePacker/bin/TexturePacker.exe"
```

The underlying TexturePacker command it runs:

```bash
TexturePacker \
  --format cocos2d \
  --data   out.plist --sheet out.png \
  --width 1024 --height 1024 \
  --algorithm Grid \
  --shape-padding 4 --border-padding 4 --extrude 2 \
  --disable-rotation --trim-mode None --trim-sprite-names \
  <normalized_frames_folder>
```

Key params:
- `--algorithm Grid` → neat N×N grid (each cell = sprite + `shape-padding`).
- `--shape-padding 4` + `--border-padding 4` → ≥8px transparent gutter between
  frames and from the sheet edge.
- `--extrude 2` → duplicates each sprite's **own** edge pixels 2px outward, so GPU
  sampling at the boundary stays the sprite's own color → kills cross-frame bleed.
- `--trim-mode None` → keeps the full `cell-prep` cell (`sourceSize=cell`, offset=0).
- `--trim-sprite-names` → plist frame keys become `name_00` .. `name_15`.

Constraint: `(cell-prep + shape-padding) × grid` must fit in `sheet`. For 4×4@1024
use `cell-prep=240` (240+4)×4 = 976 ≤ 1024. For 8×8 you'd need a larger sheet
(2048) or smaller cell-prep.

### Step B3 — (optional) Preview GIF
The wrapper also emits `<name>_preview_4x4.gif` by slicing the plist in frame order.
To parse a TexturePacker plist, read **`textureRect`** (not `frame`) and
**`textureRotated`** (not `rotated`) — see `references/cocos2d_plist_spec.md`.

### Cocos side: mipmaps
Even with gutter+extrude above, set the texture asset's **Filter Mode = Bilinear**
(not Trilinear) in the Inspector, or set `genMipmaps:false` in the `.png.meta`.
Bilinear = no mipmap sampling, doubly safe. (Trilinear samples mipmaps; with this
atlas it's still safe thanks to extrude, but Bilinear is the belt-and-suspenders
choice for 2D sequence frames.)

## Multi-variant (e.g. 8×8 + 4×4)

Run Step 1 twice with `--grid 8` and `--grid 4` (different `--out` dirs), then
Step 2 for each `.atlas`. Compare file sizes to pick the smaller atlas that still
looks acceptable, then sync the chosen PNG+plist into the Cocos `resources`
folder.

## Reference

- `references/cocos2d_plist_spec.md` — exact plist field requirements, the
  no-space-rect rule, libGDX-atlas→plist mapping, and the failure cases that
  motivated this skill. Read it whenever a plist fails to import.

## Resources

- `scripts/build_atlas.py` — ordered-frame → square transparent atlas + `.atlas`.
- `scripts/gen_plist.py` — `.atlas` → standard Cocos2d `.plist` (self-validated).
- `scripts/make_preview_gif.py` — frames folder → playback GIF.
- `scripts/build_with_texturepacker.py` — **recommended**: normalize frames then call
  TexturePacker CLI to emit a clean-edge cocos2d atlas + plist (format=3).
