from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image
import plistlib

SKILL = Path(__file__).resolve().parents[1] / "skills" / "cocos2d-atlas-builder"
BUILD = SKILL / "scripts" / "build_atlas.py"
GEN = SKILL / "scripts" / "gen_plist.py"
GIF = SKILL / "scripts" / "make_preview_gif.py"


def _make_frames(folder: Path, n: int, size: int = 64) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        im = Image.new("RGBA", (size, size), ((i * 7) % 255, 40, 200, 255))
        im.save(folder / f"frame_{i:04d}.png")


class Cocos2dAtlasBuilderTest(unittest.TestCase):
    def test_build_and_plist_4x4(self):
        src = Path(tempfile.mkdtemp()) / "frames"
        _make_frames(src, 40, 64)
        out = Path(tempfile.mkdtemp())

        r = subprocess.run(
            [sys.executable, str(BUILD), "--src", str(src), "--out", str(out),
             "--name", "cat_test", "--grid", "4", "--cell", "128"],
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, r.stderr)

        png = out / "cat_test.png"
        atlas = out / "cat_test.atlas"
        self.assertTrue(png.exists(), "atlas png missing")
        self.assertTrue(atlas.exists(), "atlas file missing")
        self.assertTrue((out / "frames").is_dir(), "frames/ missing")
        self.assertTrue((out / "preview_cat_test.png").exists(), "preview missing")

        im = Image.open(png)
        self.assertEqual(im.size, (512, 512), "4x4 @128 should be 512x512")

        plist_path = out / "cat_test.plist"
        r2 = subprocess.run(
            [sys.executable, str(GEN), "--atlas", str(atlas), "--out", str(plist_path)],
            capture_output=True, text=True,
        )
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertTrue(plist_path.exists(), "plist missing")

        with open(plist_path, "rb") as f:
            plist = plistlib.load(f)
        self.assertEqual(plist["metadata"]["format"], 2, "must be format=2")
        self.assertEqual(plist["metadata"]["pixelFormat"], "RGBA8888")
        self.assertEqual(len(plist["frames"]), 16, "4x4 -> 16 frames")

        # rect string must have NO spaces inside braces
        first = next(iter(plist["frames"].values()))
        self.assertNotIn(" ", first["frame"], "rect must not contain spaces")

    def test_build_8x8_frame_count(self):
        src = Path(tempfile.mkdtemp()) / "frames"
        _make_frames(src, 100, 32)
        out = Path(tempfile.mkdtemp())
        r = subprocess.run(
            [sys.executable, str(BUILD), "--src", str(src), "--out", str(out),
             "--name", "big", "--grid", "8", "--cell", "64"],
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        atlas = out / "big.atlas"
        r2 = subprocess.run(
            [sys.executable, str(GEN), "--atlas", str(atlas), "--out", str(out / "big.plist")],
            capture_output=True, text=True,
        )
        self.assertEqual(r2.returncode, 0, r2.stderr)
        with open(out / "big.plist", "rb") as f:
            plist = plistlib.load(f)
        self.assertEqual(len(plist["frames"]), 64, "8x8 -> 64 frames")

    def test_preview_gif(self):
        out = Path(tempfile.mkdtemp())
        frames = out / "frames"
        _make_frames(frames, 8, 32)
        gif = out / "playback.gif"
        r = subprocess.run(
            [sys.executable, str(GIF), "--frames", str(frames), "--out", str(gif),
             "--resize", "32", "--fps", "12"],
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(gif.exists(), "gif missing")

    def test_content_max_scales_and_centers(self):
        src = Path(tempfile.mkdtemp()) / "frames"
        src.mkdir(parents=True, exist_ok=True)
        # Make 16 frames: small 40x20 content on a 128x128 transparent canvas.
        for i in range(16):
            im = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
            patch = Image.new("RGBA", (40 + i, 20 + i), (255, 0, 0, 255))
            im.paste(patch, (10, 20), patch)
            im.save(src / f"frame_{i:04d}.png")
        out = Path(tempfile.mkdtemp())
        r = subprocess.run(
            [sys.executable, str(BUILD), "--src", str(src), "--out", str(out),
             "--name", "fit", "--grid", "4", "--cell", "128", "--content-max", "64"],
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        im = Image.open(out / "fit.png")
        self.assertEqual(im.size, (512, 512), "4x4 @128 -> 512x512")

        # Content should be centered: there must be some transparent margin around
        # the edges of each cell, but the center should be opaque.
        import numpy as np
        a = np.array(im.convert("RGBA"))
        cell = 128
        margins_ok = True
        centers_opaque = True
        for r in range(4):
            for c in range(4):
                sub = a[r * cell:(r + 1) * cell, c * cell:(c + 1) * cell]
                # transparent margins on all 4 borders
                if sub[0, :, 3].max() > 32 or sub[-1, :, 3].max() > 32:
                    margins_ok = False
                if sub[:, 0, 3].max() > 32 or sub[:, -1, 3].max() > 32:
                    margins_ok = False
                # center pixel opaque-ish
                if sub[cell // 2, cell // 2, 3] <= 32:
                    centers_opaque = False
        self.assertTrue(margins_ok, "content-max should leave transparent margins")
        self.assertTrue(centers_opaque, "content-max should keep content near cell center")


if __name__ == "__main__":
    unittest.main()
