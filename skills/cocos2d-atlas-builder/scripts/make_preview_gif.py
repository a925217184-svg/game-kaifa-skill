# -*- coding: utf-8 -*-
"""Build a playback GIF from an ordered folder of PNG frames.

Usage:
  python make_preview_gif.py --frames path/to/frames --out preview.gif --fps 12

Use the `frames/` directory produced by build_atlas.py, or any folder of ordered
PNG frames. With --resize (square frames assumed, e.g. atlas cells), every frame
is scaled to NxN for a compact, consistent preview.
"""
import argparse
from pathlib import Path

from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", required=True, help="directory of ordered PNG frames")
    ap.add_argument("--out", required=True, help="output .gif path")
    ap.add_argument("--fps", type=int, default=12, help="frames per second")
    ap.add_argument("--resize", type=int, default=0, help="optional square resize (0 = keep size)")
    args = ap.parse_args()

    files = sorted(Path(args.frames).glob("*.png"))
    assert files, "no PNG frames found"
    imgs = [Image.open(f).convert("RGBA") for f in files]
    if args.resize:
        imgs = [im.resize((args.resize, args.resize)) for im in imgs]

    bg = (200, 200, 200)
    rgb = [Image.new("RGB", im.size, bg) for im in imgs]
    for im, out in zip(imgs, rgb):
        out.paste(im, (0, 0), im)

    dur = int(round(1000 / args.fps))
    out_path = Path(args.out)
    rgb[0].save(out_path, save_all=True, append_images=rgb[1:],
                duration=dur, loop=0, disposal=2)
    print(f"gif={out_path} frames={len(rgb)} fps={args.fps} duration={dur}ms")


if __name__ == "__main__":
    main()
