---
name: video2dsprite
description: "Turn a 2D character still into smooth animation sprites via Lovart/Dreamina base still → 即梦 Dreamina CLI video (frames2video / image2video / multimodal2video) → ffmpeg frames → magenta OR green chroma-key (auto-detected from subject colors) → dense sampled sprites (strip/grid/GIF). Use when the user wants video-to-sprite, motion capture from generated video, smoother run/walk cycles from dense frames, or runs /video2dsprite. Requires dreamina CLI. Prefer generate2dsprite for crisp pixel sheets without video."
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
5. **Solid key-color background** on the base and preserved in the video prompt. Default **magenta `#FF00FF`**; switch to **green `#00FF00`** only when `keycheck` (Step 0B) flags the subject as red/magenta/pink/purple. Required for flood-fill chroma. Always confirm the chosen color with the user.
6. **[MODE CHOICE — ASK]** Before any generation, ask the user which Dreamina mode: **首尾帧 (`frames2video`, model-selectable, best for loops — use same image for first & last frame)** vs **全能 (`image2video` / `multimodal2video`, reference-driven)**. Also confirm the model (Step 0C table) and, for 首尾帧, the first/last frame images. Do not assume.
6. **Do not invent art with PIL/Canvas.** Base art comes from Lovart/Dreamina or a user/local still. Scripts only postprocess.
7. **Do not put experimental outputs into the game** unless the user asks to integrate.
8. **Prefer one locomotion cycle for game use.** Dense sample across a full 6s multi-cycle clip is fine for previews; for engine sheets, optionally re-sample a single cycle (12–16 frames) after visual QC.
9. **Report absolute paths** of video, cleaned frames, strips, and preview GIFs when done.

## Workflow

### 0. Setup — choose Dreamina generation mode & key color (ASK THE USER)

This step is **mandatory and interactive**. Do not start generation until the user
has chosen both the generation mode and (for 首尾帧 mode) the first/last frames,
and until the key color is decided.

#### 0A. Which generation mode?

Ask the user to pick one of:

- **首尾帧模式 (first-last frame)** → Dreamina `frames2video`
  - You pass a **first frame** and a **last frame**; Dreamina interpolates between them.
  - **Model is selectable** (see 0C).
  - **🔁 LOOP / 循环提醒**: If the user wants a seamless loop, tell them to use this
    mode with the **same image as both first and last frame** (首帧 = 尾帧). That makes
    frame 0 and frame N identical → the sprite sheet loops with no pop.
  - You must **confirm the first-frame image path and the last-frame image path** with the user before submitting.

- **全能模式 (all-around / single-or-multi reference)** → Dreamina `image2video` (single image)
  or `multimodal2video` (multi-image / video / audio reference, the web "全能参考" mode)
  - You pass one (or several) reference images + a prompt; Dreamina drives the motion.
  - **Model is selectable** (see 0C).
  - Cannot guarantee a perfect loop as easily as 首尾帧 mode; still works for one-shot motions.

#### 0B. Key color — red/magenta/purple safety check (AUTO, but confirm)

Before building the base still, run the built-in checker on the subject artwork:

```bash
python skills/video2dsprite/scripts/video2dsprite.py keycheck --image <subject.png>
```

- It estimates the subject (foreground) pixels and measures how many fall in the
  **red / magenta / pink / purple** family (the colors that collide with a
  `#FF00FF` magenta screen).
- `recommended key color: magenta` → use **magenta `#FF00FF`** background (default).
- `recommended key color: green` → the subject carries red/magenta/purple, so use a
  **green `#00FF00` screen** instead to avoid erasing the character during keying.
- If the check is ambiguous, show the user the risk value and let them override.

Pass the chosen color into every downstream step (`--key-color magenta|green|auto`).

#### 0C. Which model? (present a choice)

For 首尾帧 和 全能 modes the model is selectable. Show the user this chooser
(values are the real Dreamina CLI `model_version` set):

| 选项 | model_version | 分辨率 | 时长 | 备注 |
| --- | --- | --- | --- | --- |
| Seedance 2.5 | `seedance2.5` | 480p / 720p / 1080p | 4–30s | 画质最好，**VIP 专属**，额度最贵 |
| Seedance 2.0 VIP | `seedance2.0_vip` | 720p / 1080p / 4k | 4–15s | 高画质 + 高分辨率，VIP |
| Seedance 2.0 fast VIP | `seedance2.0fast_vip` | 720p | 4–15s | 快 + VIP，性价比高 |
| Seedance 2.0 | `seedance2.0` | 720p | 4–15s | 标准，非 VIP 也可 |
| Seedance 2.0 fast | `seedance2.0fast` | 720p | 4–15s | 最快、最省额度 |
| Seedance 2.0 mini | `seedance2.0mini` | 720p | 4–15s | 轻量、最省 |
| Seedance 1.5 pro | `seedance1.5pro` | 720p | 5–12s | 老一代 |
| Seedance 1.0 fast | `seedance1.0fast` | 720p | 5–10s | 仅 `image2video` 支持，最老 |

Defaults if the user does not care: `seedance2.0_vip` (best non-2.5 balance),
`720p`, `duration 5–6s`. Note `frames2video` does NOT offer `seedance1.0fast`.

**Cost reminder:** every generation consumes Dreamina credits (`dreamina user_credit`).
Confirm the mode + model + frames with the user, then generate.

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

- Full body visible, generous background margin
- Side view for run/walk (profile or 3/4 side), feet near bottom third
- Same art style as the rest of the project when a reference exists
- No text, UI, watermark, or second character
- **Background color = the key color from Step 0B**: `#FF00FF` magenta (default) **or** `#00FF00` green (when the subject has red/magenta/purple). Prompt the generator for a flat solid background of that exact color.

Save as `<out_dir>/base/<name>-base.png` (magenta) or note the green variant explicitly.

Write the exact image prompt into `prompt-used.txt`.

### 3. Animate with Dreamina CLI

**[COST NOTIFY]** Tell the user: backend=**Dreamina CLI**, mode (首尾帧 / 全能), model, duration, resolution, estimated cost. Wait for acknowledgment.

Pick the command based on **Step 0A**:

#### 3A. 首尾帧模式 → `dreamina frames2video`

```bash
dreamina frames2video \
  --first  <out_dir>/base/<name>-first.png \
  --last   <out_dir>/base/<name>-last.png \
  --prompt "character transitions from the first pose to the last pose in place, locked camera, flat solid #FF00FF background, stable identity..." \
  --model_version seedance2.0_vip \
  --duration 6 \
  --video_resolution 720p \
  --output <out_dir>/video/<name>-6s.mp4
```

- **Confirm `--first` and `--last` image paths with the user** (Step 0A).
- **For a seamless loop**, use the **same image for both** `--first` and `--last` (首帧=尾帧).
- `--model_version` is freely selectable from the Step 0C table (`seedance1.0fast` is NOT supported here).
- Keep the **background color matching Step 0B** (`#FF00FF` magenta or `#00FF00` green) in the prompt.

#### 3B. 全能模式 → `dreamina image2video` (single image) or `multimodal2video` (multi reference)

```bash
# single image
dreamina image2video \
  --image <out_dir>/base/<name>-base.png \
  --prompt "side-view character running in place on flat solid #FF00FF background, 6 seconds, locked camera, stable identity..." \
  --model_version seedance2.0_vip \
  --duration 6 \
  --video_resolution 720p \
  --output <out_dir>/video/<name>-6s.mp4

# multi-reference ("全能参考"): image + optional video/audio
dreamina multimodal2video \
  --image <out_dir>/base/<name>-base.png \
  --prompt "..." --model_version seedance2.0_vip --duration 6 --video_resolution 720p \
  --output <out_dir>/video/<name>-6s.mp4
```

Mandatory motion constraints in the prompt (all modes):

- Subject moves **in place** (treadmill style) — no travel across frame
- Camera **locked** — no pan, zoom, or orbit
- Background stays **flat solid** (the Step 0B key color)
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
  --fps 0 \
  --key-color auto
```

Notes:

- `--fps 0` = extract every decoded frame (use source fps)
- `--key-color auto` (default) auto-detects magenta vs green from the raw frame corners; you can also force `magenta` or `green` to match Step 0B.
- Chroma flood-fill from corners + despill; green uses a green despill path, magenta uses the magenta path.
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

Optional: check a subject image for red/magenta/purple before you build the base still:

```bash
python skills/video2dsprite/scripts/video2dsprite.py keycheck --image <subject.png>
# -> recommended key color: magenta | green
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

- Mode: **首尾帧 (`frames2video`)** when a loop is wanted; otherwise **全能 (`image2video`)**
- Model: **`seedance2.0_vip`**, `720p`, `duration 6`
- Key color: **magenta `#FF00FF`** unless `keycheck` flags red/magenta/purple → **green `#00FF00`**
- Duration: **6s**
- Action: **side run in place**, facing right
- Export counts: **8, 16, 24, 48**
- Cell: **128²**, body height ~100, feet at y≈118
- Prefer `dreamina frames2video` (首尾帧) for loops; `image2video`/`multimodal2video` for one-shot reference-driven motion

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
