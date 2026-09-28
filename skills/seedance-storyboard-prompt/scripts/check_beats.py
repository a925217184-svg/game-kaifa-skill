# -*- coding: utf-8 -*-
"""
Seedance 分镜提示词 · 节拍与镜数自检工具
（配合 count_chars.py 使用：前者验算术，后者数字数）

检查项（规范 §3.7.1 / §3.7.6）：
  1. 镜数是否落在预算区间（镜数 ≈ 总时长 ÷ 2.0，±2）
  2. 单镜目标时长是否 ≥1.5s（低于即违规，必须合并）
  3. 节奏行写出的秒数是否全为 0.5s 粒度（0.15 / 0.6 / 0.7 这类禁止）
  4. 收势段动作完成点 X + 静止时长 Y 是否 = 生成档位总长（默认 5）
  5. 起幅 ≥0.3s；收势（镜长 − X）≥0.3s；起幅 ≤ X
  6. 镜长 − X（收势在裁切区间内的长度）是否 ≥0.3s
  7. 收势段是否写了「静止持续到最后一帧」
  8. 正文是否复述全局负面约束（逐镜重复的负面词）
  9. 是否存在连续 3 镜同构（镜头字段机位相同）

用法：
    python check_beats.py <提示词文件.txt> [--total 15.0]
    --total  目标总时长（秒），用于核 Σ 与镜数区间；不填则用各镜之和
"""

import io
import re
import sys
import argparse
from collections import Counter

SHOT_SPLIT = re.compile(r"\n\s*====\s*\n")
SEC = re.compile(r"(\d+(?:\.\d+)?)\s*(?:s|秒)")


def parse(path):
    t = io.open(path, encoding="utf-8").read().replace("\r\n", "\n")
    t = t.split("以上为【可复制区】结束")[0]
    t = t.split("以下为【说明区】")[0]
    blocks = [b.strip() for b in SHOT_SPLIT.split(t) if b.strip()]
    shots = []
    for b in blocks:
        m = re.search(r"Shot\s*(\d+)", b)
        if not m:
            continue
        n = m.group(1)
        lens = re.search(r"^镜头：(.*)$", b, re.M)
        dur = re.search(r"时长：\s*(\d+):(\d+(?:\.\d+)?)\s*-\s*(\d+):(\d+(?:\.\d+)?)\s*秒", b)
        beat = re.search(r"^节奏：(.*)$", b, re.M)
        body = re.search(r"^拍摄内容：(.*?)(?=^节奏：|^同期声：|\Z)", b, re.M | re.S)
        if not dur:
            shots.append({"n": n, "err": "缺少可解析的「时长：MM:SS.s-MM:SS.s 秒」行"})
            continue
        start = int(dur.group(1)) * 60 + float(dur.group(2))
        end = int(dur.group(3)) * 60 + float(dur.group(4))
        shots.append({
            "n": n,
            "dur": round(end - start, 2),
            "lens": (lens.group(1).strip() if lens else ""),
            "beat": (beat.group(1).strip() if beat else ""),
            "body": (body.group(1).strip() if body else ""),
        })
    return shots


def check(shots, total=None):
    fails, warns = [], []
    if any("err" in s for s in shots):
        for s in shots:
            if "err" in s:
                fails.append(f"Shot {s['n']}：{s['err']}")
        return fails, warns

    n_shots = len(shots)
    tot = round(sum(s["dur"] for s in shots), 2)
    target = total if total else tot

    if total and abs(tot - total) > 0.5:
        fails.append(f"Σ 各镜 {tot}s 与目标 {total}s 相差 {round(abs(tot-total),2)}s（允许 ±0.5s）")

    lo, hi = max(1, round(target / 2.0) - 2), round(target / 2.0) + 2
    if not (lo <= n_shots <= hi):
        fails.append(
            f"镜数 {n_shots} 超出预算区间 {lo}–{hi}（目标 {target}s ÷ 2.0 ±2）——切太碎，先合并")

    for s in shots:
        n, dur, beat = s["n"], s["dur"], s["beat"]
        tag = f"Shot {n}"
        if dur < 1.5:
            fails.append(f"{tag}：目标时长 {dur}s < 1.5s 下限，必须并入相邻镜")
        if not beat:
            fails.append(f"{tag}：缺「节奏：」行")
            continue

        nums = [float(x) for x in SEC.findall(beat)]
        if len(nums) < 3:
            fails.append(f"{tag}：节奏行格式不完整（需 起幅 a / 完成点 X / 静止时长 Y 三个秒数）")
            continue
        bad = [x for x in re.findall(r"(\d+(?:\.\d+)?)\s*(?:s|秒)", beat)
               if abs((float(x) * 10) % 5) > 1e-6]
        if bad:
            fails.append(f"{tag}：含非 0.5s 粒度的秒数 {bad}——节奏行写出的秒数一律取 0.5s 粒度")

        a, X, Y = nums[0], nums[1], nums[2]
        if abs(X + Y - 5) > 0.01:
            warns.append(f"{tag}：X({X}) + Y({Y}) = {round(X+Y,2)} ≠ 5，若非 5s 档请忽略")
        c = round(dur - X, 2)
        if a > X + 1e-9:
            fails.append(f"{tag}：起幅 {a}s 大于动作完成点 {X}s")
        if a < 0.3 - 1e-9:
            fails.append(f"{tag}：起幅 {a}s < 0.3s")
        if c < 0.3 - 1e-9:
            fails.append(f"{tag}：收势 {c}s（= 镜长 {dur}s − X {X}s）< 0.3s")
        if not re.search(r"静止持续到最后一帧|holds still for the final frames", beat):
            fails.append(f"{tag}：收势段缺「画面静止持续到最后一帧 / holds still for the final frames」")

    # 全局负面约束逐镜复述检测
    neg_words = ["无第四人", "禁止第一人称", "无未点名角色", "无多余人物", "纯音效无 BGM"]
    for w in neg_words:
        hits = [s["n"] for s in shots if w in s["body"]]
        if len(hits) >= 3:
            fails.append(f"全局负面约束「{w}」在 {len(hits)} 个镜的正文里复述（{hits}）——只在全局锁写一次")

    # 连续 3 镜同构检测（取镜头字段的机位片段做 key）
    keys = []
    for s in shots:
        seg = re.sub(r"虚拟\d+mm.*?，", "", s["lens"])
        seg = re.sub(r"[，,].*?焦点[^，,]*", "", seg)
        keys.append(seg.strip()[:40])
    run, prev = 1, None
    for i, k in enumerate(keys):
        if k and k == prev:
            run += 1
            if run == 3:
                fails.append(
                    f"Shot {shots[i-2]['n']}-{shots[i]['n']} 连续 3 镜镜头字段同构"
                    f"（{k}）——机位相同只换环境元素时必须合并")
        else:
            run = 1
        prev = k

    return fails, warns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--total", type=float, default=None, help="目标总时长（秒）")
    args = ap.parse_args()

    shots = parse(args.file)
    if not shots:
        print("未解析到任何 Shot 段（检查是否用独立一行 ==== 分隔）")
        sys.exit(1)

    fails, warns = check(shots, args.total)
    tot = round(sum(s.get("dur", 0) for s in shots), 2)

    print(f"文件：{args.file}")
    print(f"镜数 {len(shots)}｜Σ {tot}s" + (f"（目标 {args.total}s）" if args.total else ""))
    print("-" * 62)
    print(f"{'镜':>6} {'镜长':>7} {'起幅':>6} {'动作X':>7} {'收势':>6} {'静止Y':>7}")
    for s in shots:
        nums = [float(x) for x in SEC.findall(s.get("beat", ""))]
        if len(nums) >= 3:
            a, X, Y = nums[:3]
            c = round(s["dur"] - X, 2)
            print(f"{s['n']:>6} {s['dur']:>6}s {a:>6} {X:>7} {c:>6} {Y:>7}")
        else:
            print(f"{s['n']:>6} {s.get('dur', 0):>6}s   （节奏行缺失或格式不符）")
    print("-" * 62)

    if warns:
        print("提示：")
        for w in warns:
            print("  ~", w)
    if fails:
        print(f"不通过 {len(fails)} 项：")
        for f in fails:
            print("  X", f)
        sys.exit(1)
    print("节拍自检全部通过（镜数 / 镜长 / 0.5s 粒度 / X+Y=5 / 收势定格 / 同构 / 负面复述）")


if __name__ == "__main__":
    main()
