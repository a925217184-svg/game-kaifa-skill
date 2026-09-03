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
```

Outputs in `--out`:
- `cat_pink.png` — square transparent atlas (grid×cell px).
- `cat_pink.atlas` — libGDX-style frame map (consumed by Step 2).
- `frames/` — individual resized frames (use for the preview GIF).
- `preview_cat_pink.png` — grid preview with frame indices.

Behavior notes:
- Frame count is forced to `grid×grid`. First source frame = atlas frame 0, last
  source frame = atlas last frame (forced unless `--no-keep-ends`). Middle frames
  are uniformly sampled in playback order so the loop is smooth.
- Every frame is LANCZOS-resized to `--cell`, preserving relative position → no
  jump between frames.
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
