# -*- coding: utf-8 -*-
"""Build a square transparent sprite atlas (N×N grid) from an ordered list of PNG frames.

Inputs:
  - a directory of ordered PNG frames (transparent / already keyed)

Outputs to --out:
  - <name>.png   : packed square atlas, transparent background (RGBA)
  - <name>.atlas : libGDX-style atlas describing each frame rect (consumed by gen_plist.py)
  - frames/      : individual resized frames (handy for GIF preview / inspection)
  - preview_<name>.png : grid preview sheet with frame indices

This is the generic core of the "cocos2d-atlas-builder" skill. The cat-specific
keying / green-screen step is NOT included here — feed already-keyed transparent
frames in. Designed to be deterministic and reusable across projects.

The atlas keeps playback order: frame 0 = first source frame, last frame = last
source frame (forced unless --no-keep-ends). Middle frames are uniformly sampled
so the animation loops smoothly.
"""
import argparse
import shutil
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def load_ordered(src: Path):
    return sorted(src.glob("*.png"))


def defringe_green(im: Image.Image) -> Image.Image:
    """Knock out leftover green-screen fringe (only semi-opaque green pixels)."""
    a = np.array(im.convert("RGBA"))
    rgb = a[:, :, :3].astype(np.float32)
    G, R, B = rgb[:, :, 1], rgb[:, :, 0], rgb[:, :, 2]
    greenish = (G - R > 50) & (G - B > 50) & (a[:, :, 3] > 32)
    a[greenish, 3] = 0
    return Image.fromarray(a, "RGBA")


def key_black_bg(im: Image.Image, thr: int = 40) -> Image.Image:
    """Make a near-black background transparent.

    Dark pixels are only treated as background when they are connected to the
    image border, so genuinely dark parts of the subject (hair, eyes, shoes)
    stay opaque. Uses a border-seeded flood fill (no extra deps).
    """
    from collections import deque
    a = np.array(im.convert("RGBA"))
    h, w = a.shape[:2]
    lum = a[:, :, :3].max(axis=2)
    dark = lum < thr
    mask = np.zeros((h, w), dtype=bool)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if dark[y, x]:
                mask[y, x] = True
                q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if dark[y, x] and not mask[y, x]:
                mask[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not mask[ny, nx] and dark[ny, nx]:
                mask[ny, nx] = True
                q.append((ny, nx))
    a[mask, 3] = 0
    return Image.fromarray(a, "RGBA")


def fit_content_to_cell(im: Image.Image, cell: int, content_max: int, alpha_thr: int = 32) -> Image.Image:
    """Scale the sprite content so its longest side == content_max and paste it
    centered in a transparent cell×cell canvas.

    This makes sprites from different sources occupy the same visual proportion
    inside the atlas cell, even if their original canvas sizes or framing differ.
    """
    a = np.array(im.convert("RGBA"))
    ys, xs = np.where(a[:, :, 3] > alpha_thr)
    if len(xs) == 0:
        return Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
    x1, x2 = xs.min(), xs.max()
    y1, y2 = ys.min(), ys.max()
    cropped = Image.fromarray(a[y1:y2 + 1, x1:x2 + 1], "RGBA")
    cw, ch = cropped.size
    scale = content_max / max(cw, ch)
    new_w, new_h = int(round(cw * scale)), int(round(ch * scale))
    scaled = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
    ox = (cell - new_w) // 2
    oy = (cell - new_h) // 2
    canvas.paste(scaled, (ox, oy), scaled)
    return canvas


def sample_indexes(N, grid, keep_ends=True):
    """Pick grid*grid frame indices in playback order.
    keep_ends forces first frame=0 and last frame=N-1.

    When the source has FEWER frames than the target grid (N <= total), we
    interpolate across the source with `total` samples (duplicates allowed) and
    force the two ends, so we still emit exactly `total` frames and the loop
    still keeps the first/last keyframes.
    """
    total = grid * grid
    if keep_ends:
        if N <= total:
            idx = [int(round(x)) for x in np.linspace(0, N - 1, total)]
            idx[0], idx[-1] = 0, N - 1
            return idx
        interior = sorted(set(int(round(x)) for x in np.linspace(1, N - 2, total - 2)))
        while len(interior) < total - 2:  # rare rounding collisions -> backfill
            for x in range(1, N - 1):
                if x not in interior:
                    interior.append(x)
                    break
            interior = sorted(interior)
        return [0] + interior + [N - 1]
    # keep_ends=False: sample `total` indices evenly across the source
    return [int(round(x)) for x in np.linspace(0, N - 1, total)]


def build_atlas(name, frames, out_dir, grid, cell, make_frames=True, make_preview=True):
    n = len(frames)
    assert n == grid * grid, f"{name}: need {grid * grid} frames, got {n}"
    w = h = grid * cell
    canvas = np.zeros((h, w, 4), np.uint8)  # transparent
    entries = []
    for i, fr in enumerate(frames):
        r, c = divmod(i, grid)
        x, y = c * cell, r * cell
        canvas[y:y + cell, x:x + cell] = np.array(fr)
        entries.append((f"{name}_{i:04d}", x, y))
    atlas = Image.fromarray(canvas, "RGBA")
    atlas_path = out_dir / f"{name}.png"
    atlas.save(atlas_path)

    lines = [f"{name}.png", f"size: {w},{h}", "format: RGBA8888",
             "filter: Linear,Linear", "repeat: none", ""]
    for fname, x, y in entries:
        lines += [fname, "  rotate: false", f"  xy: {x}, {y}",
                  f"  size: {cell}, {cell}", f"  orig: {cell}, {cell}",
                  "  offset: 0, 0", "  index: -1", ""]
    (out_dir / f"{name}.atlas").write_text("\n".join(lines), encoding="utf-8")

    if make_frames:
        fdir = out_dir / "frames"
        if fdir.exists():
            fdir.rename(out_dir / f"frames_bak_{int(time.time())}")
        fdir.mkdir(exist_ok=True)
        for i, fr in enumerate(frames):
            fr.save(fdir / f"{name}_{i:04d}.png")
    else:
        # never leave a stale frames/ behind
        fdir = out_dir / "frames"
        if fdir.exists():
            fdir.rename(out_dir / f"frames_bak_{int(time.time())}")

    return atlas_path


def build_preview(name, frames, out_dir, grid, cell=110):
    sheet = np.full((grid * cell, grid * cell, 3), 200, np.uint8)
    for i, fr in enumerate(frames):
        r, c = divmod(i, grid)
        thumb = fr.resize((cell, cell), Image.Resampling.LANCZOS)
        ta = np.array(thumb)
        a = ta[:, :, 3:4].astype(np.float32) / 255.0
        region = sheet[r * cell:(r + 1) * cell, c * cell:(c + 1) * cell]
        comp = (ta[:, :, :3].astype(np.float32) * a + region * (1 - a)).astype(np.uint8)
        d = Image.fromarray(comp)
        ImageDraw.Draw(d).text((2, 2), str(i), fill=(0, 0, 0))
        sheet[r * cell:(r + 1) * cell, c * cell:(c + 1) * cell] = np.array(d)
    pv = Image.fromarray(sheet)
    pv_path = out_dir / f"preview_{name}.png"
    pv.save(pv_path)
    return pv_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="directory of ordered PNG frames (already keyed/transparent)")
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--name", default=None, help="atlas base name (default: source dir name)")
    ap.add_argument("--grid", type=int, default=4, help="N for N×N grid (e.g. 4 -> 16 frames, 8 -> 64)")
    ap.add_argument("--cell", type=int, default=256, help="cell size in px (each frame resized to cell×cell)")
    ap.add_argument("--no-keep-ends", action="store_true", help="do not force first/last frame preservation")
    ap.add_argument("--defringe-green", action="store_true", help="knock out leftover green-screen fringe")
    ap.add_argument("--key-black", action="store_true",
                    help="make near-black background transparent (border-connected flood fill)")
    ap.add_argument("--no-frames", action="store_true",
                    help="do not emit the resized frames/ subfolder (atlas + .atlas only)")
    ap.add_argument("--no-preview", action="store_true",
                    help="do not emit the preview_<name>.png grid sheet")
    ap.add_argument("--content-max", type=int, default=None,
                    help="fit sprite content so its longest side == N px, then center it in the cell. "
                         "Use this when sprites from different sources look different sizes in the atlas.")
    args = ap.parse_args()

    src = Path(args.src)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    name = args.name or src.name

    srcs = load_ordered(src)
    # Re-run safety: when --out == --src, a previously generated atlas PNG/atlas
    # would otherwise be globbed as a "frame". Ignore any file whose stem matches
    # the output base name so only true source frames are packed.
    srcs = [s for s in srcs if s.stem != name]
    N = len(srcs)
    idx = sample_indexes(N, args.grid, keep_ends=not args.no_keep_ends)
    assert len(idx) == args.grid * args.grid
    if not args.no_keep_ends:
        assert idx[0] == 0 and idx[-1] == N - 1, "首/尾帧未保留"

    frames = []
    for k in idx:
        im = Image.open(srcs[k]).convert("RGBA")
        if args.key_black:
            im = key_black_bg(im)
        elif args.defringe_green:
            im = defringe_green(im)
        if args.content_max:
            im = fit_content_to_cell(im, args.cell, args.content_max)
        else:
            im = im.resize((args.cell, args.cell), Image.Resampling.LANCZOS)
        frames.append(im)

    atlas_path = build_atlas(name, frames, out_dir, args.grid, args.cell,
                             make_frames=not args.no_frames,
                             make_preview=not args.no_preview)

    a = np.array(Image.open(atlas_path).convert("RGBA"))
    tail = ""
    if not args.no_preview:
        pv = build_preview(name, frames, out_dir, args.grid)
        tail = f" preview={pv.name}"
    print(f"atlas={atlas_path} {a.shape[1]}x{a.shape[0]} corner_alpha={int(a[0, 0, 3])} "
          f"frames={len(frames)}{tail}")


if __name__ == "__main__":
    main()
