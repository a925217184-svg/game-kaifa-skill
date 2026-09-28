# -*- coding: utf-8 -*-
"""
Seedance 分镜提示词 · 节拍与镜数自检工具（v3.1 · 时间标记穿插格式）
（配合 count_chars.py 使用：前者验算术，后者数字数）

格式约定（v3.1，2026-09-28 定稿）：
    ① 每个 Shot 标题行带绝对时间段：Shot 04｜00:04.8-00:06.8（1.6 秒）
    ② 「拍摄内容」把时间标记**穿插在描述句流里**（不单独起「时序」段、不用 ｜ 分隔）：
        拍摄内容：<机位+光照起句>。0.0-0.5s <起幅，站位/表情挂这里>。0.5-1.0s <主体动作>，
                  一气呵成做完即停；1.0-5.0s 画面完全静止、无任何运动，持续到最后一帧 /
                  holds still for the final frames。
    （两个历史格式仍可解析：v3 的「时序 …｜描述」写法、v2 的「节奏：」行 + 「时长：」行）

检查项：
  1. 镜数是否落在预算区间（镜数 ≈ 总时长 ÷ 2.0，±2）
  2. 单镜目标时长是否 ≥1.5s（低于即违规，必须合并）
  3. 时间标记是否从 0.0s 起、逐段首尾相接无缝隙、按时间顺序出现
  4. 所有秒数是否全为 0.5s 粒度（0.15 / 0.6 / 0.7 这类禁止）
  5. 动作完成点 X + 其后静止 Y 是否 = 生成档位总长（默认 5）
  6. 起幅 ≥0.3s；收势（镜长 − X）≥0.3s；起幅 ≤ X
  7. 末段是否写了「静止」且带「静止持续到最后一帧 / holds still for the final frames」
  8. 动作段是否有「做完即停 / 一气呵成」（防模型把动作铺满整个窗口）
  9. 正文是否复述全局负面约束（逐镜重复的负面词）
 10. 是否存在连续 3 镜同构（镜头字段机位相同）

用法：
    python check_beats.py <提示词文件.txt> [--total 15.0]
    --total  目标总时长（秒），用于核 Σ 与镜数区间；不填则用各镜之和
"""

import io
import re
import sys
import argparse

SHOT_SPLIT = re.compile(r"\n\s*====\s*\n")
RANGE = re.compile(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*s")
ANY_SEC = re.compile(r"(\d+(?:\.\d+)?)\s*(?:s|秒)")
TITLE_TIME = re.compile(
    r"Shot\s*(\d+)\s*[｜|]\s*(\d+):(\d+(?:\.\d+)?)\s*-\s*(\d+):(\d+(?:\.\d+)?)"
    r"\s*[（(]\s*([\d.]+)\s*秒")
LEGACY_DUR = re.compile(r"时长：\s*(\d+):(\d+(?:\.\d+)?)\s*-\s*(\d+):(\d+(?:\.\d+)?)\s*秒")
STILL_PHRASE = re.compile(r"静止持续到最后一帧|holds still for the final frames")
DONE_WORDS = ("做完即停", "一气呵成", "完成即停")


def spans_of(body):
    """返回 [(起, 止, match_start, match_end), ...]，按出现顺序（＝时间顺序）。"""
    return [(float(m.group(1)), float(m.group(2)), m.start(), m.end())
            for m in RANGE.finditer(body)]


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
        body = re.search(r"^拍摄内容：(.*?)(?=^同期声：|\Z)", b, re.M | re.S)
        body = body.group(1).strip() if body else ""

        tt = TITLE_TIME.search(b)
        leg = LEGACY_DUR.search(b)
        if tt:
            start = int(tt.group(2)) * 60 + float(tt.group(3))
            end = int(tt.group(4)) * 60 + float(tt.group(5))
            mode = "inline"
        elif leg:
            start = int(leg.group(1)) * 60 + float(leg.group(2))
            end = int(leg.group(3)) * 60 + float(leg.group(4))
            mode = "legacy"
        else:
            shots.append({"n": n, "mode": "?", "err":
                          "缺时间轴——标题行需写成 Shot NN｜MM:SS.s-MM:SS.s（X 秒），或旧版「时长：」行"})
            continue

        shots.append({
            "n": n,
            "mode": mode,
            "dur": round(end - start, 2),
            "lens": (lens.group(1).strip() if lens else ""),
            "spans": spans_of(body) if mode == "inline" else [],
            "beat": (re.search(r"^节奏：(.*)$", b, re.M).group(1).strip()
                     if re.search(r"^节奏：(.*)$", b, re.M) else ""),
            "body": body,
        })
    return shots


def check_inline(s, tag, fails, warns):
    body = s["body"]
    sp = s["spans"]
    if not sp:
        fails.append(f"{tag}：「拍摄内容」里找不到时间标记——应穿插写成 "
                     f"`0.0-0.5s …；0.5-1.0s …；1.0-5.0s 画面完全静止…`")
        return None
    if len(sp) < 2:
        fails.append(f"{tag}：只用到了 {len(sp)} 个时间标记，至少要「起幅 / 动作 / 静止」三段推进")
        return None

    bad = sorted({v for a, b, _, _ in sp for v in (a, b)
                  if abs((v * 10) % 5) > 1e-6})
    if bad:
        fails.append(f"{tag}：时间标记含非 0.5s 粒度的秒数 {bad}——一律取 0.5s 粒度")

    if abs(sp[0][0]) > 1e-9:
        fails.append(f"{tag}：第一个时间标记没从 0.0s 起（实际从 {sp[0][0]}s 起）")
    for a, b, _, _ in sp:
        if b <= a + 1e-9:
            fails.append(f"{tag}：时间标记 {a}-{b}s 区间写反了")
    for i in range(len(sp) - 1):
        if abs(sp[i][1] - sp[i + 1][0]) > 1e-9:
            fails.append(f"{tag}：时间标记不连续——{sp[i][1]}s 到 {sp[i+1][0]}s 之间有缝"
                         f"（应按时间顺序首尾相接）")
    for i in range(len(sp) - 1):
        if sp[i + 1][0] < sp[i][0] - 1e-9:
            fails.append(f"{tag}：时间标记没按时间顺序排——{sp[i][0]}s 后面出现了 {sp[i+1][0]}s")

    a = sp[0][1]
    X, last_end = sp[-1][0], sp[-1][1]
    Y = round(last_end - X, 2)
    if a < 0.3 - 1e-9:
        fails.append(f"{tag}：起幅 {a}s < 0.3s")
    if a > X + 1e-9:
        fails.append(f"{tag}：起幅 {a}s 大于动作完成点 {X}s")
    c = round(s["dur"] - X, 2)
    if c < 0.3 - 1e-9:
        fails.append(f"{tag}：收势 {c}s（= 镜长 {s['dur']}s − 动作完成点 {X}s）< 0.3s")
    if abs(X + Y - 5) > 0.01:
        warns.append(f"{tag}：动作完成点 X({X}) + 其后静止 Y({Y}) = {round(X + Y, 2)} ≠ 5，"
                     f"若非 5s 档请忽略")

    tail = body[sp[-1][3]:]
    if "静止" not in tail:
        fails.append(f"{tag}：最后一个时间标记后没写「画面完全静止」")
    if not STILL_PHRASE.search(body):
        fails.append(f"{tag}：末段缺「静止持续到最后一帧 / holds still for the final frames」")
    mid = body[sp[0][3]:sp[-1][2]]
    if not any(w in mid for w in DONE_WORDS):
        warns.append(f"{tag}：动作段建议加「一气呵成做完即停」——否则模型会把动作铺满整个窗口")
    return a, X, c, Y


def check_legacy(s, tag, fails, warns):
    beat = s["beat"]
    if not beat:
        fails.append(f"{tag}：缺「节奏：」行")
        return None
    nums = [float(x) for x in ANY_SEC.findall(beat)]
    if len(nums) < 3:
        fails.append(f"{tag}：节奏行格式不完整（需 起幅 a / 完成点 X / 静止时长 Y 三个秒数）")
        return None
    bad = [x for x in ANY_SEC.findall(beat) if abs((float(x) * 10) % 5) > 1e-6]
    if bad:
        fails.append(f"{tag}：含非 0.5s 粒度的秒数 {bad}")
    a, X, Y = nums[0], nums[1], nums[2]
    c = round(s["dur"] - X, 2)
    if a < 0.3 - 1e-9:
        fails.append(f"{tag}：起幅 {a}s < 0.3s")
    if c < 0.3 - 1e-9:
        fails.append(f"{tag}：收势 {c}s < 0.3s")
    if not STILL_PHRASE.search(beat):
        fails.append(f"{tag}：收势段缺「静止持续到最后一帧 / holds still for the final frames」")
    if abs(X + Y - 5) > 0.01:
        warns.append(f"{tag}：X({X}) + Y({Y}) = {round(X+Y, 2)} ≠ 5，若非 5s 档请忽略")
    return a, X, c, Y


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
        fails.append(f"Σ 各镜 {tot}s 与目标 {total}s 相差 {round(abs(tot-total), 2)}s（允许 ±0.5s）")

    lo, hi = max(1, round(target / 2.0) - 2), round(target / 2.0) + 2
    if not (lo <= n_shots <= hi):
        fails.append(f"镜数 {n_shots} 超出预算区间 {lo}–{hi}（目标 {target}s ÷ 2.0 ±2）——切太碎，先合并")

    for s in shots:
        tag = f"Shot {s['n']}"
        if s["dur"] < 1.5:
            fails.append(f"{tag}：目标时长 {s['dur']}s < 1.5s 下限，必须并入相邻镜")
        if s["mode"] == "inline":
            check_inline(s, tag, fails, warns)
        else:
            check_legacy(s, tag, fails, warns)

    neg_words = ["无第四人", "禁止第一人称", "无未点名角色", "无多余人物", "纯音效无 BGM"]
    for w in neg_words:
        hits = [s["n"] for s in shots if w in s["body"]]
        if len(hits) >= 3:
            fails.append(f"全局负面约束「{w}」在 {len(hits)} 个镜的正文里复述（{hits}）——只在全局锁写一次")

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


def stats(s):
    if s["mode"] == "inline":
        sp = s["spans"]
        if len(sp) >= 2:
            a = sp[0][1]
            X, last_end = sp[-1][0], sp[-1][1]
            return a, X, round(s["dur"] - X, 2), round(last_end - X, 2)
    nums = [float(x) for x in ANY_SEC.findall(s.get("beat", ""))]
    if len(nums) >= 3:
        a, X, Y = nums[:3]
        return a, X, round(s["dur"] - X, 2), Y
    return None


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
    modes = {s.get("mode") for s in shots}

    print(f"文件：{args.file}")
    print(f"镜数 {len(shots)}｜Σ {tot}s" + (f"（目标 {args.total}s）" if args.total else "")
          + ("｜格式：" + ("时间标记穿插" if modes == {"inline"} else "旧版节奏行" if modes == {"legacy"} else "混合")))
    print("-" * 62)
    print(f"{'镜':>6} {'镜长':>7} {'起幅':>6} {'动作X':>7} {'收势':>6} {'静止Y':>7}")
    for s in shots:
        st = stats(s)
        if st:
            a, X, c, Y = st
            print(f"{s['n']:>6} {s['dur']:>6}s {a:>6} {X:>7} {c:>6} {Y:>7}")
        else:
            print(f"{s['n']:>6} {s.get('dur', 0):>6}s   （时间标记/节奏行缺失或格式不符）")
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
    print("节拍自检全部通过（镜数 / 镜长 / 0.5s 粒度 / 时间标记连续且有序 / X+Y=5 / 静止到末帧 / 同构 / 负面复述）")


if __name__ == "__main__":
    main()
