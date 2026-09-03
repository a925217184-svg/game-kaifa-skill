# -*- coding: utf-8 -*-
"""Generate a Cocos2d-compatible .plist from a libGDX-style .atlas file.

The emitted plist strictly follows the Free Texture Packer "Cocos2d" export
template (verified to load in Cocos Creator / cocos2d-x). See
references/cocos2d_plist_spec.md for the full rationale and failure cases.

Usage:
  python gen_plist.py --atlas path/to/name.atlas --out path/to/name.plist

The script self-validates the output with plistlib so a malformed plist is
caught immediately instead of later in the Cocos importer.
"""
import argparse
from pathlib import Path

import plistlib


def parse_atlas(path: Path):
    lines = path.read_text(encoding="utf-8").split("\n")
    tex = lines[0].strip()
    size = None
    frames = {}
    i = 1
    while i < len(lines):
        line = lines[i]
        if line.strip() == "":
            i += 1
            continue
        if line.startswith("size:"):
            size = line.split(":", 1)[1].strip()
            i += 1
            continue
        if not line.startswith(" "):
            name = line.strip()
            j = i + 1
            block = []
            while j < len(lines) and lines[j].startswith(" "):
                block.append(lines[j].strip())
                j += 1
            d = {}
            for bl in block:
                if ":" in bl:
                    k, v = bl.split(":", 1)
                    d[k.strip()] = v.strip()
            if "xy" in d:
                frames[name] = d
            i = j
        else:
            i += 1
    return tex, size, frames


def to_plist(tex, size, frames):
    # Strictly aligned with the Free Texture Packer "Cocos2d" template.
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">',
           '<plist version="1.0">', '  <dict>', '    <key>frames</key>', '    <dict>']
    for name, d in frames.items():
        xy, sz, off, orig = d["xy"], d["size"], d["offset"], d["orig"]
        rotated = "true" if d.get("rotate", "false") == "true" else "false"
        # NOTE: rect/offset/size strings MUST contain NO spaces, or Cocos regex fails.
        fs = "{{" + xy.replace(" ", "") + "},{" + sz.replace(" ", "") + "}}"  # {{x,y},{w,h}}
        scs = "{{0,0},{" + sz.replace(" ", "") + "}}"                         # {{0,0},{w,h}}
        offs = "{" + off.replace(" ", "") + "}"
        szs = "{" + orig.replace(" ", "") + "}"
        out += [f'      <key>{name}</key>', '      <dict>',
                '        <key>frame</key>', '        <string>' + fs + '</string>',
                '        <key>offset</key>', '        <string>' + offs + '</string>',
                '        <key>rotated</key>', '        <' + rotated + '/>',
                '        <key>sourceColorRect</key>', '        <string>' + scs + '</string>',
                '        <key>sourceSize</key>', '        <string>' + szs + '</string>',
                '      </dict>']
    ms = "{" + size.replace(" ", "") + "}"
    out += ['    </dict>', '    <key>metadata</key>', '    <dict>',
            '      <key>format</key>', '      <integer>2</integer>',
            '      <key>pixelFormat</key>', '      <string>RGBA8888</string>',
            '      <key>premultiplyAlpha</key>', '      <false/>',
            '      <key>realTextureFileName</key>', f'      <string>{tex}</string>',
            '      <key>size</key>', f'      <string>{ms}</string>',
            '      <key>textureFileName</key>', f'      <string>{tex}</string>',
            '    </dict>', '  </dict>', '</plist>']
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--atlas", required=True, help="input .atlas file (from build_atlas.py)")
    ap.add_argument("--out", default=None, help="output .plist (default: same name, .plist)")
    args = ap.parse_args()
    atlas_p = Path(args.atlas)
    out_p = Path(args.out) if args.out else atlas_p.with_suffix(".plist")
    tex, size, frames = parse_atlas(atlas_p)
    plist = to_plist(tex, size, frames)
    out_p.write_text(plist, encoding="utf-8")
    # self-validation
    try:
        plistlib.loads(plist.encode("utf-8"))
        valid = "OK"
    except Exception as e:  # noqa: BLE001
        valid = f"PARSE-FAIL:{e}"
    print(f"plist={out_p.name} frames={len(frames)} format=2 RGBA8888 -> {valid}")


if __name__ == "__main__":
    main()
