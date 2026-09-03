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


if __name__ == "__main__":
    unittest.main()
