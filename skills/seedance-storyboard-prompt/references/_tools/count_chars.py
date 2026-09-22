# -*- coding: utf-8 -*-
"""
Seedance 提示词字数自检工具

平台硬限制：单次提交的提示词 ≤ 2000 字。
本脚本按「全局锁 + 目标 Shot 正文」为一段（即用户实际复制粘贴的一段）统计字数，
输出每段的：总字符数（含标点空格）/ 去空白字符数 / 是否超限。

用法：
    python count_chars.py <提示词文件.txt> [--limit 2000]
"""
import io, os, re, sys

LIMIT = 2000


def split_blocks(text):
    """按 ==== 分隔线切成块；第一块若含【全局锁】则视为全局锁段"""
    parts = re.split(r"\n\s*====\s*\n", text)
    blocks = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        # 截断说明区
        for marker in ["以下为说明区", "———— 以下为【说明区】"]:
            if marker in p:
                p = p.split(marker)[0].strip()
        if p:
            blocks.append(p)
    return blocks


def stats(s):
    total = len(s)
    nospace = len(re.sub(r"\s+", "", s))
    return total, nospace


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    limit = LIMIT
    for a in sys.argv[1:]:
        if a.startswith("--limit"):
            limit = int(a.split("=")[1])
    if not args:
        print(__doc__)
        return
    path = args[0]
    text = io.open(path, encoding="utf-8").read()
    blocks = split_blocks(text)
    if not blocks:
        print("未识别到内容块")
        return
    lock = ""
    if "【全局锁】" in blocks[0]:
        lock = blocks[0]
        shots = blocks[1:]
    else:
        shots = blocks

    lt, ln = stats(lock)
    print("文件：%s" % os.path.basename(path))
    print("全局锁段：%d 字（去空白 %d 字）" % (lt, ln))
    print("-" * 62)
    print("%-10s %-12s %-12s %s" % ("段", "总字符", "去空白", "判定"))
    worst = 0
    for i, s in enumerate(shots, 1):
        name = s.split("\n")[0][:16]
        t, n = stats(lock + "\n\n" + s) if lock else stats(s)
        worst = max(worst, n)
        flag = "OK" if n <= limit else "超限 %d 字" % (n - limit)
        print("%-10s %-12d %-12d %s" % (name, t, n, flag))
    print("-" * 62)
    print("上限 %d 字；最长一段（去空白）%d 字 → %s" % (limit, worst, "全部通过" if worst <= limit else "存在超限，需压缩"))


if __name__ == "__main__":
    main()
