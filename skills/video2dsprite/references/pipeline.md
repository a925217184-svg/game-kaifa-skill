# Video2dsprite pipeline

## End-to-end

```text
1. base still          image_gen / image_edit / existing PNG on #FF00FF
2. video               image_to_video  (6s default, 10s optional)
3. frames-raw          ffmpeg decode all frames (or fixed fps)
4. frames-clean        magenta flood-fill + light despill → RGBA
5. sample              even indices for N in {8,16,24,48}
6. normalize           crop alpha bbox → scale body height → feet line
7. export              sprite_XX.png, strip, grid, preview GIF
8. meta                pipeline-meta.json + README.txt
```

## Suggested folder layout

```text
<out_dir>/
  base/<name>-base.png
  video/<name>-6s.mp4
  frames-raw/frame_0001.png ...
  frames-clean/clean_0000.png ...
  sprite/
    sprite_01.png ...          # default small set if requested
    x16/sprite_01.png ...
    x24/...
    x48/...
    run-strip-8.png
    run-strip-16.png
    run-preview-24.gif
    ...
  prompt-used.txt
  pipeline-meta.json
  README.txt
```

## ffmpeg extract

Processor shells out to `ffmpeg` when available:

```bash
ffmpeg -y -i video.mp4 -vsync 0 frames-raw/frame_%04d.png
```

If ffmpeg is missing, fail with a clear install message. Do not invent frames.

## Chroma key

1. **Key color decision (Step 0B):** run `python video2dsprite.py keycheck --image <subject>`.
   - `recommended magenta` → use `#FF00FF` screen (default).
   - `recommended green` → the subject carries red/magenta/pink/purple, so use `#00FF00` green screen instead.
2. Treat near-key pixels as key candidates (distance to the chosen key color + channel boost: magenta = high R+B/low G; green = high G/low R,B).
3. Flood-fill from image corners so interior key-colored costume bits (e.g. a magenta scarf on a magenta screen) are less likely to vanish.
4. Despill residual fringes toward neutral/transparent along the correct axis (magenta → pull R+B; green → pull G).
5. Write RGBA PNGs.

The `process` / `clean` commands accept `--key-color magenta|green|auto`; `auto` detects from the raw frame corners.

## Sampling

Even spacing including first and last:

```text
idx[i] = round(i * (total - 1) / (want - 1))  for i in 0..want-1
```

Export multiple `want` values in one run so the user can compare smoothness vs softness.

## Normalize (feet anchor)

1. Alpha bbox of cleaned frame
2. Scale so content height ≈ `body_height` (default 100 in a 128 cell)
3. Paste so bottom of content sits at `foot_y` (default 118)
4. Center horizontally

For `center` anchor, place bbox center at cell center instead.

## GIF duration defaults

| Frames | ms / frame (approx) |
| --- | --- |
| 8 | 80 |
| 16 | 60 |
| 24 | 40 |
| 48 | 25 |

Goal: roughly 0.6–1.2s visual loop for previews (not necessarily matching source video realtime).

## When not to use this pipeline

- Need hard pixel edges and fixed multi-row grids → `$generate2dsprite`
- Map props / tilesets → `$generate2dmap` + `$generate2dsprite`
- Non-Grok agent without `image_to_video`
- User wants production-perfect hero kit with many actions — video path is locomotion experiment first
