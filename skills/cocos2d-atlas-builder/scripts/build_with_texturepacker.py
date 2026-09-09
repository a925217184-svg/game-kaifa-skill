# -*- coding: utf-8 -*-
"""
build_with_texturepacker.py — 用 TexturePacker 标准做法出「干净边缘」的 cocos2d 图集。

为什么优先用 TexturePacker 而不是纯 Python 手写 plist：
- 它能原生输出标准 cocos2d plist（format=3 / RGBA8888 / premultiplyAlpha=false），Cocos Creator 直接导入；
- 它的 --shape-padding / --border-padding / --extrude 是业界处理「切单帧边缘脏线 / 串帧」的标准手段：
  相邻精灵之间留透明 gutter + 把每帧自身边缘像素外扩喂给 GPU 采样，
  即使 Cocos 开了 mipmap，缩小显示时也绝不会切到邻帧内容。

流程：
A) 归一化每一帧：裁到 alpha 包围盒 -> 按最大内容边统一缩放 -> 居中(水平)/脚底对齐(垂直)进固定 cell 画布；
   （不同来源、视觉大小不一的帧用这个来拉齐）
B) 保持原图比例 / 不裁切像素（推荐用于「同源等尺寸序列帧」，消除帧间跳动）：
   整帧按【全局唯一 scale】统一缩放后居中拼接，相对大小/位置锁定，循环播放角色不抖。
   传 --keep-ratio --pad 4 即可启用。
2) 把归一化后的帧（命名 name_00..name_15）喂给 TexturePacker CLI，出 图集 PNG + plist；
3) （可选）按 plist 帧序切片生成循环预览 GIF，肉眼核对。

用法（推荐：同源等尺寸序列帧，零跳动拼接）：
  python build_with_texturepacker.py \
    --src  /path/to/ordered_frames \
    --out  /path/to/out \
    --name passerby_1_happy \
    --grid 4 --sheet 1024 --cell-prep 240 \
    --keep-ratio --pad 4 \
    --tp "C:/Program Files/CodeAndWeb/TexturePacker/bin/TexturePacker.exe"

用法（不同来源、需拉齐视觉大小）：
  python build_with_texturepacker.py \
    --src  /path/to/ordered_frames \
    --out  /path/to/out \
    --name passerby_1_happy \
    --grid 4 --sheet 1024 \
    --content-max 224 --cell-prep 240 \
    --tp "C:/Program Files/CodeAndWeb/TexturePacker/bin/TexturePacker.exe"

依赖：pillow, numpy, 以及本机已安装/授权 TexturePacker（CLI）。
"""
import os
import sys
import glob
import shutil
import tempfile
import argparse
import subprocess
import numpy as np
from PIL import Image


# ---- TexturePacker 自动探测 ----
def find_texturepacker(explicit=None):
    if explicit:
        return explicit
    candidates = [
        r"C:\Program Files\CodeAndWeb\TexturePacker\bin\TexturePacker.exe",
        r"C:\Program Files (x86)\CodeAndWeb\TexturePacker\bin\TexturePacker.exe",
        "/Applications/TexturePacker.app/Contents/MacOS/TexturePacker",
        "texturepacker",  # on PATH (macOS/Linux)
    ]
    for c in candidates:
        if os.path.exists(c) or c == "texturepacker":
            return c
    return None


def load_frames(folder):
    paths = sorted(glob.glob(os.path.join(folder, "*.png")))
    return paths, [Image.open(p).convert("RGBA") for p in paths]


def decimate(n_total, n_target):
    """保持第 0 帧与第 total-1 帧（首尾，循环关键），只从中间帧 [1, total-2] 均匀抽帧。

    用于序列帧循环：首尾帧是循环闭合的接缝，必须原样保留、不可删减；
    中间的 (n_target-2) 个槽位全部从 interior 区间取样，绝不触碰首尾。
    """
    if n_target >= n_total:
        return list(range(n_total))
    if n_target <= 2:
        return [0, n_total - 1][:n_target]
    interior = list(range(1, n_total - 1))      # 仅中间帧
    need = n_target - 2
    step = (len(interior) - 1) / (need - 1)
    chosen, used = [], set()
    for i in range(need):
        idx = int(round(i * step))
        while idx in used:                        # 极端情况下的去重回退
            idx = (idx + 1) % len(interior)
        used.add(idx)
        chosen.append(interior[idx])
    return [0] + chosen + [n_total - 1]


def prep_frame(im, cell_prep, content_max, alpha_thr=30, bottom_pad=8):
    """裁到内容框 -> 统一缩放 -> 居中(水平)/脚底对齐(垂直)进 cell_prep 透明画布。"""
    a = np.asarray(im.split()[3])
    ys, xs = np.where(a > alpha_thr)
    if len(xs) == 0:
        return Image.new("RGBA", (cell_prep, cell_prep), (0, 0, 0, 0))
    bx0, by0, bx1, by1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    cropped = im.crop((bx0, by0, bx1, by1))
    cw, ch = cropped.size
    scale = content_max / max(cw, ch)
    sw, sh = max(1, round(cw * scale)), max(1, round(ch * scale))
    scaled = cropped.resize((sw, sh), Image.LANCZOS)
    canvas = Image.new("RGBA", (cell_prep, cell_prep), (0, 0, 0, 0))
    px = (cell_prep - sw) // 2
    py = cell_prep - bottom_pad - sh
    canvas.alpha_composite(scaled, (px, py))
    return canvas


def prep_keep_ratio(im, cell_prep, scale, pad=4):
    """保持原图比例、不裁切像素：整帧按全局统一 scale 缩放后居中进 cell_prep 透明画布。

    与 prep_frame 的区别：不做 alpha 包围盒裁切，也不按各自内容重定尺寸。
    所有帧用同一个 scale（由全局最长边决定），因此帧间相对大小/位置完全锁定，
    循环播放时角色不会跳动（无缩放差、无位移差）。
    """
    w, h = im.size
    sw, sh = max(1, round(w * scale)), max(1, round(h * scale))
    scaled = im.resize((sw, sh), Image.LANCZOS)
    canvas = Image.new("RGBA", (cell_prep, cell_prep), (0, 0, 0, 0))
    px = (cell_prep - sw) // 2
    py = (cell_prep - sh) // 2
    canvas.alpha_composite(scaled, (px, py))
    return canvas


def build_preview_gif(plist_path, png_path, gif_path, ms=120):
    import plistlib, re
    d = plistlib.load(open(plist_path, "rb"))
    sheet = Image.open(png_path).convert("RGBA")
    keys = sorted(d["frames"].keys(),
                  key=lambda k: int(re.search(r"(\d+)$", k).group(1)))
    frames = []
    for k in keys:
        fr = d["frames"][k]
        m = re.findall(r"\d+", fr["textureRect"])
        x, y, w, h = int(m[0]), int(m[1]), int(m[2]), int(m[3])
        cell = sheet.crop((x, y, x + w, y + h)).convert("RGBA")
        if fr.get("textureRotated"):
            cell = cell.rotate(90, expand=True)
        frames.append(cell.resize((256, 256), Image.LANCZOS))
    g = []
    for c in frames:
        alpha = c.split()[3]
        p = c.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=255)
        mask = alpha.point(lambda a: 255 if a <= 32 else 0)
        p.paste(255, mask=mask)
        p.info["transparency"] = 255
        g.append(p)
    g[0].save(gif_path, save_all=True, append_images=g[1:],
              duration=ms, loop=0, disposal=2, transparency=255)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="有序透明 PNG 序列帧目录")
    ap.add_argument("--out", required=True, help="输出目录")
    ap.add_argument("--name", required=True, help="图集基名(同时作帧名前缀), 如 passerby_1_happy")
    ap.add_argument("--grid", type=int, default=4, help="N×N 网格, 默认 4 (16 帧)")
    ap.add_argument("--sheet", type=int, default=1024, help="图集边长, 默认 1024")
    ap.add_argument("--content-max", type=int, default=224, help="归一化后角色最长边像素(仅 --keep-ratio 关闭时生效)")
    ap.add_argument("--cell-prep", type=int, default=240, help="归一化画布边长(需 +padding 后 ≤ sheet 能排下 grid 列)")
    ap.add_argument("--keep-ratio", action="store_true",
                    help="保持每张原图比例、不裁切像素：全局统一缩放后居中拼接(消除帧间跳动)")
    ap.add_argument("--pad", type=int, default=4, help="keep-ratio 模式下画布内边距(像素)")
    ap.add_argument("--tp", default=None, help="TexturePacker 可执行文件路径")
    ap.add_argument("--shape-padding", type=int, default=4)
    ap.add_argument("--border-padding", type=int, default=4)
    ap.add_argument("--extrude", type=int, default=2)
    ap.add_argument("--no-gif", action="store_true", help="跳过预览 GIF")
    args = ap.parse_args()

    tp = find_texturepacker(args.tp)
    if not tp:
        sys.exit("找不到 TexturePacker，请用 --tp 指定可执行文件路径。")
    if shutil.which(tp) is None and not os.path.exists(tp):
        sys.exit("TexturePacker 路径无效: %s" % tp)

    nframes = args.grid * args.grid
    # cell_prep + shape_padding 必须能在 sheet 里排成 grid 列
    if (args.cell_prep + args.shape_padding) * args.grid > args.sheet:
        sys.exit("cell-prep(%d)+shape-padding(%d) 放不下 %d 列@%d。请调小 --cell-prep 或 --shape-padding。"
                 % (args.cell_prep, args.shape_padding, args.grid, args.sheet))

    paths, imgs = load_frames(args.src)
    total = len(imgs)
    if total == 0:
        sys.exit("源目录无 PNG: %s" % args.src)
    picks = decimate(total, nframes)
    assert picks[0] == 0 and picks[-1] == total - 1, "首/尾帧未保留!"

    # 全局统一缩放因子（keep-ratio 模式）：由所有入选帧的最大边长决定，
    # 保证每张帧用同一个 scale -> 帧间比例/位置锁定，循环不跳动。
    if args.keep_ratio:
        max_dim = max(max(imgs[i].size) for i in picks)
        scale = (args.cell_prep - 2 * args.pad) / max_dim
        prep_fn = lambda im: prep_keep_ratio(im, args.cell_prep, scale, args.pad)
    else:
        prep_fn = lambda im: prep_frame(im, args.cell_prep, args.content_max)

    os.makedirs(args.out, exist_ok=True)
    # 每次跑都用全新的唯一临时目录(落在系统 temp，自清理)写入归一化帧，避免：
    # ① 删旧文件触发沙箱「批量删除保护」；② 上一轮残留文件污染 TexturePacker 输入；
    # ③ 在输出目录留下 _tp_prep_* 垃圾目录。
    work = tempfile.mkdtemp(prefix="_tp_prep_%s_" % args.name)
    for i, idx in enumerate(picks):
        prep_fn(imgs[idx]).save(
            os.path.join(work, "%s_%02d.png" % (args.name, i)))

    out_png = os.path.join(args.out, "%s_atlas_%dx%d.png" % (args.name, args.grid, args.grid))
    out_plist = os.path.join(args.out, "%s_atlas_%dx%d.plist" % (args.name, args.grid, args.grid))

    cmd = [
        tp, "--format", "cocos2d",
        "--data", out_plist, "--sheet", out_png,
        "--width", str(args.sheet), "--height", str(args.sheet),
        "--algorithm", "Grid",
        "--shape-padding", str(args.shape_padding),
        "--border-padding", str(args.border_padding),
        "--extrude", str(args.extrude),
        "--disable-rotation",
        "--trim-mode", "None", "--trim-sprite-names",
        work,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if r.returncode != 0 or not os.path.exists(out_plist):
        sys.exit("TexturePacker 失败:\n%s\n%s" % (r.stdout, r.stderr))

    if not args.no_gif:
        build_preview_gif(out_plist, out_png,
                          os.path.join(args.out, "%s_preview_%dx%d.gif" % (args.name, args.grid, args.grid)))

    import plistlib
    d = plistlib.load(open(out_plist, "rb"))
    meta = d["metadata"]
    print("OK %s -> PNG=%dKB plist帧=%d size=%s premult=%s" % (
        args.name, os.path.getsize(out_png) // 1024, len(d["frames"]),
        meta.get("size"), meta.get("premultiplyAlpha")))


if __name__ == "__main__":
    main()
