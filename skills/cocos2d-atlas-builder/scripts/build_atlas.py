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


def sample_indexes(N, grid, keep_ends=True):
    """Pick grid*grid frame indices in playback order.
    keep_ends forces first frame=0 and last frame=N-1."""
    total = grid * grid
    if N <= total:
        return list(range(N))
    if keep_ends:
        interior = sorted(set(int(round(x)) for x in np.linspace(1, N - 2, total - 2)))
        while len(interior) < total - 2:  # rare rounding collisions -> backfill
            for x in range(1, N - 1):
                if x not in interior:
                    interior.append(x)
                    break
            interior = sorted(interior)
        return [0] + interior + [N - 1]
    return list(range(total))


def build_atlas(name, frames, out_dir, grid, cell):
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

    fdir = out_dir / "frames"
    if fdir.exists():
        fdir.rename(out_dir / f"frames_bak_{int(time.time())}")
    fdir.mkdir(exist_ok=True)
    for i, fr in enumerate(frames):
        fr.save(fdir / f"{name}_{i:04d}.png")

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
    args = ap.parse_args()

    src = Path(args.src)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    name = args.name or src.name

    srcs = load_ordered(src)
    N = len(srcs)
    idx = sample_indexes(N, args.grid, keep_ends=not args.no_keep_ends)
    assert len(idx) == args.grid * args.grid
    if not args.no_keep_ends:
        assert idx[0] == 0 and idx[-1] == N - 1, "首/尾帧未保留"

    frames = []
    for k in idx:
        im = Image.open(srcs[k]).convert("RGBA")
        if args.defringe_green:
            im = defringe_green(im)
        im = im.resize((args.cell, args.cell), Image.Resampling.LANCZOS)
        frames.append(im)

    atlas_path = build_atlas(name, frames, out_dir, args.grid, args.cell)
    pv = build_preview(name, frames, out_dir, args.grid)

    a = np.array(Image.open(atlas_path).convert("RGBA"))
    print(f"atlas={atlas_path} {a.shape[1]}x{a.shape[0]} corner_alpha={int(a[0, 0, 3])} "
          f"frames={len(frames)} preview={pv.name}")


if __name__ == "__main__":
    main()
