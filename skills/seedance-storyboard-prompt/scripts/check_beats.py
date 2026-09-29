# -*- coding: utf-8 -*-
"""
check_beats.py —— Seedance 2.0 官方式提示词自检（v4）

用法：
    python check_beats.py <文件.txt>

校验项（对应《规则卡 v4》第五节自查清单）：
  1. 每条声明了生成时长（4-15 秒）
  2. 时间线用整数秒、1 秒粒度、从 0 起、段与段首尾相接
  3. 末段止点 == 该条生成时长
  4. 每条结尾有「整体…」收尾句
  5. 角色已用 @图片N / @视频N 锚定
  6. 字数：官方上限 2000 字（2026-09-29 官方更新；官方案例仍 80-250 字，
     写长可以，但每句都要为画面付费）
  7. 全篇无已废止的旧写法（时序 / 做完即停 / 完全静止 / 三字段 / 5 秒档…）
  8. 各条时长之和 == 目标总时长（--total 给出时校验）

退出码非 0 即有违规。
"""
import re
import sys

# ---- 时间线标记：0-1秒画面： / 0–1秒： / 0-1秒， ----
MARK = re.compile(r"(\d+(?:\.\d+)?)\s*[-–—]\s*(\d+(?:\.\d+)?)\s*秒")
# ---- 条标题：【第 1 条 · 生成时长选 5 秒】 ----
CLIP_HEAD = re.compile(r"【\s*第\s*(\d+)\s*条[^\n]*?】")
DUR_IN_HEAD = re.compile(r"生成时长\s*选?\s*(\d+(?:\.\d+)?)\s*秒")
DUR_INLINE = re.compile(r"（\s*(\d+(?:\.\d+)?)\s*秒\s*）")

DEPRECATED = [
    ("时序",                 "旧 v3/v3.1 的「时序」节拍块，v4 已废止"),
    ("一气呵成做完即停",     "旧 v2 的「做完即停」，v4 已废止"),
    ("做完即停",             "旧 v2 的「做完即停」，v4 已废止"),
    ("持续到最后一帧",       "旧 v2 的「静止到末帧」，仅首尾帧循环视频保留"),
    ("holds still",          "旧 v2 的英文静止句，v4 已废止"),
    ("按 5 秒档生成",        "官方是 4-15s 自选，不存在必须按 5 秒档"),
    ("只取前",               "官方是 4-15s 自选，不用生成 5 秒再裁"),
    ("拍摄内容：",           "旧三字段结构，v4 改为一段自然语言"),
    ("同期声：",             "旧三字段结构，v4 改为一段自然语言"),
    ("节奏：",               "旧节拍字段，v4 并入「整体…」收尾句"),
    ("技巧依据",             "过程性元信息，属说明区，不得进可复制区"),
]

SEP = "================【以上为【可复制区】结束"


def split_clips(copy_area):
    """按【第 N 条】切分，返回 [(标题, 正文)]"""
    heads = list(CLIP_HEAD.finditer(copy_area))
    if not heads:
        return []
    clips = []
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(copy_area)
        clips.append((h.group(0), copy_area[h.end():end]))
    return clips


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    total = None
    if "--total" in sys.argv:
        idx = sys.argv.index("--total")
        if idx + 1 < len(sys.argv):
            total = float(sys.argv[idx + 1])

    raw = open(path, encoding="utf-8").read()
    copy_area = raw.split(SEP)[0] if SEP in raw else raw

    errs, warns = [], []

    # ---- 7. 废止写法扫描（只扫可复制区）----
    for word, why in DEPRECATED:
        if word in copy_area:
            errs.append("可复制区出现已废止写法「%s」——%s" % (word, why))

    clips = split_clips(copy_area)
    if not clips:
        errs.append("没找到【第 N 条】标记——v4 要求每条以「【第 N 条 · 生成时长选 X 秒】」开头")
        report(errs, warns, path)
        return 1

    sum_dur = 0.0
    for idx, (head, body) in enumerate(clips, 1):
        tag = "第 %d 条" % idx
        # 1. 生成时长
        m = DUR_IN_HEAD.search(head) or DUR_INLINE.search(head)
        if not m:
            errs.append("%s：标题没写生成时长（应写成【第 N 条 · 生成时长选 X 秒】）" % tag)
            dur = None
        else:
            dur = float(m.group(1))
            sum_dur += dur
            if not (4 <= dur <= 15):
                errs.append("%s：生成时长 %.1fs 超出官方 4-15s 范围" % (tag, dur))
            if dur != int(dur):
                warns.append("%s：生成时长建议写整数秒" % tag)

        # 2/3. 时间线
        marks = [(float(a), float(b)) for a, b in MARK.findall(body)]
        if not marks:
            errs.append("%s：没有时间线标记（应写「0-1秒画面：…」）" % tag)
        else:
            for a, b in marks:
                if a != int(a) or b != int(b):
                    errs.append("%s：时间线出现小数秒 %.1f-%.1f —— 官方只用整数秒、1 秒粒度"
                                % (tag, a, b))
            if abs(marks[0][0]) > 1e-6:
                errs.append("%s：时间线不是从 0 起（首段起点 %.1f）" % (tag, marks[0][0]))
            for i in range(1, len(marks)):
                if abs(marks[i][0] - marks[i - 1][1]) > 1e-6:
                    errs.append("%s：时间线不连续——上一段止 %.1f，下一段起 %.1f"
                                % (tag, marks[i - 1][1], marks[i][0]))
            last_end = marks[-1][1]
            if dur is not None and abs(last_end - dur) > 1e-6:
                errs.append("%s：末段止点 %.1fs 与生成时长 %.1fs 对不上" % (tag, last_end, dur))
            seg = [b - a for a, b in marks]
            if min(seg) < 1:
                errs.append("%s：存在不足 1 秒的段（最短 %.1fs）——官方最小粒度是 1 秒" % (tag, min(seg)))

        # 4. 整体收尾句
        if "整体" not in body:
            warns.append("%s：缺少「整体…」收尾句（色调/光影/节奏/声音/排除项打包）" % tag)

        # 5. 素材锚定
        if not re.search(r"@(图片|图|视频|音频)\s*\d", body):
            warns.append("%s：没有 @图片N / @视频N 素材锚定" % tag)

        # 6. 字数
        n = len(re.sub(r"\s", "", body))
        if n > 2000:
            errs.append("%s：正文 %d 字，超过官方 2000 字上限——拆成两条" % (tag, n))
        elif n > 1200:
            warns.append("%s：正文 %d 字（官方上限 2000）——确认每句都在为画面付费，"
                         "别堆同义形容词" % (tag, n))
        elif n < 80:
            warns.append("%s：正文仅 %d 字，可能信息量不足" % (tag, n))

    # 8. 总时长
    if total is not None and abs(sum_dur - total) > 0.51:
        errs.append("各条时长之和 %.1fs 与目标 %.1fs 不符" % (sum_dur, total))
    else:
        print("各条时长之和：%.1f 秒" % sum_dur)

    report(errs, warns, path)
    return 1 if errs else 0


def report(errs, warns, path):
    print("文件：%s" % path)
    if warns:
        print("\n[提醒 %d]" % len(warns))
        for w in warns:
            print("  ! " + w)
    if errs:
        print("\n[违规 %d]" % len(errs))
        for e in errs:
            print("  x " + e)
        print("\n节拍自检未通过。")
    else:
        print("\n节拍自检全部通过（整数秒 / 1 秒粒度 / 从 0 起 / 首尾相接 / 末段止点对得上 / "
              "时长在 4-15s / 字数达标 / 无废止写法）")


if __name__ == "__main__":
    sys.exit(main())
