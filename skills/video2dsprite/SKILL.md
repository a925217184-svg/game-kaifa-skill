---
name: video2dsprite
description: "Turn a 2D character still into smooth animation sprites via Lovart/Dreamina base still → 即梦 Dreamina CLI video (image2video/multiframe2video) → ffmpeg frames → magenta chroma-key → dense sampled sprites (strip/grid/GIF). Use when the user wants video-to-sprite, motion capture from generated video, smoother run/walk cycles from dense frames, or runs /video2dsprite. Requires dreamina CLI (installed at ~/bin/dreamina.exe). Prefer generate2dsprite for crisp pixel sheets without video."
---

# Video2dsprite (Dreamina CLI video pipeline)

Convert a **base 2D character image** into **dense animation sprites** using **即梦 Dreamina CLI** for video generation.

```text
base still (Lovart/Dreamina) → dreamina image2video (in-place motion) → ffmpeg extract frames → chroma key → sample/normalize → strip / grid / GIF
```

## Prerequisites (read first)

| Requirement | Status |
| --- | --- |
| **dreamina CLI** | Must be installed (`dreamina --version` should work). Install: `curl -s https://jimeng.jianying.com/cli \| bash` |
| **dreamina login** | Must be authenticated (OAuth device flow). Run `dreamina login` once |
| **ffmpeg** | Required for frame extraction (already on this system) |
| **Lovart / Dreamina for base still** | Used to generate the initial character still on solid #FF00FF background |

If `dreamina` is not installed or not logged in, **stop** and guide the user to install/login first. Do not fake motion with code-drawn frames.

This skill is an **optional denser-motion path**. It does **not** replace `$generate2dsprite`:

| Use `$generate2dsprite` when… | Use `$video2dsprite` when… |
| --- | --- |
| Crisp pixel sheets, fixed grids, identity-critical heroes | User wants denser intermediate poses / smoother feeling loops |
| Attack/cast body sheets, prop packs, engine atlases | Experimenting with video-sourced run/walk/idle motion |
| Production default for most game sprites | User explicitly asks for video → frames → sprites |

Video softens pixels, drifts identity, and leaves chroma fringes. Always QC; for production heroes, prefer `$generate2dsprite` unless the user wants the video look.

## Parameters

Infer from the user request:

- `subject`: character / creature description, or path to existing still
- `action`: `run` | `walk` | `idle` | `attack` | custom motion phrase
- `view`: usually `side` (side-scroller). `topdown` is harder — warn and keep camera locked
- `duration`: `6` (default) or `10` seconds
- `frame_counts`: which denser sets to export, default `8,16,24,48`
- `cell_size`: output sprite cell, default `128`
- `anchor`: `feet` (default for side locomotion) | `center`
- `bg`: solid `#FF00FF` (required for chroma)
- `name`: output slug
- `out_dir`: working folder (default `./sprites/video2dsprite/<name>/` or project-relative)

## Agent rules

1. **Dreamina CLI required.** Verify `dreamina --version` works before starting. If not installed, guide the user.
2. **Still → video, never text-to-video alone.** Stage frame 1 as a clean still via **Lovart backend** or **Dreamina CLI** (`dreamina text2image` / `dreamina image2image`). Then call `dreamina image2video` for animation.
3. **[COST NOTIFY]** Before generating the base still AND before generating video, tell the user: backend, mode, what you're generating, estimated cost (Dreamina consumes account credits; check with `dreamina user_credit`). **Wait for acknowledgment before each generation.**
4. **In-place motion.** Prompt for run/walk **in place** facing a fixed direction. No camera pan, no background scroll, no scene change. Subject stays roughly centered.
5. **Solid magenta background** on the base and preserved in the video prompt (`#FF00FF` / pure magenta). Required for flood-fill chroma.
6. **Do not invent art with PIL/Canvas.** Base art comes from Lovart/Dreamina or a user/local still. Scripts only postprocess.
7. **Do not put experimental outputs into the game** unless the user asks to integrate.
8. **Prefer one locomotion cycle for game use.** Dense sample across a full 6s multi-cycle clip is fine for previews; for engine sheets, optionally re-sample a single cycle (12–16 frames) after visual QC.
9. **Report absolute paths** of video, cleaned frames, strips, and preview GIFs when done.

## Workflow

### 1. Plan

Pick the smallest useful run:

- Side-view run/walk loop → this skill
- Multi-action hero kit → still use `$generate2dsprite` per action; only use video for locomotion if requested
- FX / projectile / prop packs → `$generate2dsprite`, not video

Create:

```text
<out_dir>/
  base/
  video/
  frames-raw/
  frames-clean/
  sprite/          # default 8-frame set + denser x16/x24/x48
  prompt-used.txt
  pipeline-meta.json
  README.txt
```

### 2. Build the base still

**[COST NOTIFY]** Tell the user: backend (Lovart/Dreamina), mode, what (base still), estimated cost. Wait for acknowledgment.

Options:

- **A. Existing sprite:** open with image tools / read image, composite onto solid `#FF00FF` if needed
- **B. New character:** Use **Lovart backend** or **`dreamina text2image`** with solid magenta background, full body, side view, centered
- **C. Match reference:** Use **`dreamina image2image`** from user reference onto magenta, preserve identity

Base requirements:

- Full body visible, generous magenta margin
- Side view for run/walk (profile or 3/4 side), feet near bottom third
- Same art style as the rest of the project when a reference exists
- No text, UI, watermark, or second character

Save as `<out_dir>/base/<name>-base.png`.

Write the exact image prompt into `prompt-used.txt`.

### 3. Animate with Dreamina CLI (`image2video`)

**[COST NOTIFY]** Tell the user: backend=**Dreamina CLI**, what (video animation), duration, estimated cost. Wait for acknowledgment.

Call **即梦 Dreamina CLI**:

```bash
dreamina image2video \
  --input <out_dir>/base/<name>-base.png \
  --prompt "side-view character running in place on solid magenta background, 6 seconds, locked camera, stable identity..." \
  --duration 6 \
  --output <out_dir>/video/<name>-6s.mp4
```

For multi-image reference (e.g. first frame + last frame):

```bash
dreamina multiframe2video \
  --input <out_dir>/base/<name>-base.png,<out_dir>/base/<name>-lastframe.png \
  --prompt "character runs from idle pose to run pose in place..." \
  --duration 6 \
  --output <out_dir>/video/<name>-6s.mp4
```

Mandatory motion constraints in the prompt:

- Subject runs/walks **in place** (treadmill style)
- Camera **locked** — no pan, zoom, or orbit
- Background stays **flat solid magenta**
- Identity, costume, palette stable for the whole shot
- Single continuous action only

Check Dreamina credits before generating: `dreamina user_credit`

If `dreamina` is not installed or not logged in, stop and guide the user.

### 4. Extract + chroma + sample (local script)

Run the processor (ffmpeg + Pillow + numpy):

```bash
python skills/video2dsprite/scripts/video2dsprite.py process \
  --video <out_dir>/video/<name>-6s.mp4 \
  --out-dir <out_dir> \
  --name <name> \
  --frame-counts 8,16,24,48 \
  --cell-size 128 \
  --body-height 100 \
  --foot-y 118 \
  --fps 0
```

Notes:

- `--fps 0` = extract every decoded frame (use source fps)
- Magenta flood-fill from corners + despill
- Even sampling for each count in `--frame-counts`
- Feet-normalized cells, horizontal strip, grid, loop GIF per count

Optional: only re-sample denser sets from existing cleaned frames:

```bash
python skills/video2dsprite/scripts/video2dsprite.py sample \
  --clean-dir <out_dir>/frames-clean \
  --out-dir <out_dir> \
  --frame-counts 16,24,48 \
  --cell-size 128
```

### 5. QC

Visually check:

- [ ] Preview GIF loops without huge pops
- [ ] Magenta gone (no solid pink blocks); fringe acceptable or re-key
- [ ] Feet stay on a stable baseline (no hop from bad crop)
- [ ] Identity roughly stable (face/clothes not morphing every frame)
- [ ] Action is in-place (not sliding out of frame)
- [ ] For game use: pick one count (often **16 or 24**) or cut one true cycle

If identity drifts hard or pixels are too soft, fall back to `$generate2dsprite` for production sheets and keep the video set as motion reference only.

### 6. Deliver

Report paths only (unless user asked to wire into a game):

- Video: `video/*.mp4`
- Dense sprites: `sprite/x16|x24|x48/`
- Strips / grids / GIFs: `sprite/run-strip-N.png`, `run-grid-N.png`, `run-preview-N.gif`
- Meta: `pipeline-meta.json`

Do **not** modify game code unless requested.

## Defaults

- Duration: **6s**
- Action: **side run in place**, facing right
- Export counts: **8, 16, 24, 48**
- Cell: **128²**, body height ~100, feet at y≈118
- Background: **#FF00FF**
- Prefer `dreamina image2video` over `dreamina multiframe2video` (compose multi-ref with `dreamina image2image` first if needed)

## Tradeoffs (tell the user once)

**Pros:** denser intermediates → often feels smoother than 4–8 discrete gen poses.  
**Cons:** softer pixels, identity drift, chroma fringe, multi-cycle 6s clips are not a single perfect loop, heavier assets.  
**Rule of thumb:** 8→16→24 usually gains smoothness; 48 is often diminishing returns; 145 raw frames are for sampling, not all for runtime.

## Resources

- [references/prompt-rules.md](references/prompt-rules.md) — base still + video prompts
- [references/pipeline.md](references/pipeline.md) — folder layout, ffmpeg, sampling strategy
- [scripts/video2dsprite.py](scripts/video2dsprite.py) — extract, chroma, normalize, export

## Relationship to other skills

- `$generate2dsprite` — primary sheet pipeline (Lovart/Dreamina image generation)
- `$generate2dmap` — maps; not used here
- `$video2dsprite` — **Dreamina CLI video** motion densification path
