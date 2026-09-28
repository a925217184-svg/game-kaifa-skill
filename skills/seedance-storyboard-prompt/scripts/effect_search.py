#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
镜头/特效写法查询库检索工具（变身 / 觉醒 / 尺度潜降 等跨镜头特效序列写法）
与 cinematic-techniques 的 search.py 互补：那库查单镜头语言，本库查多镜头特效序列/转场写法。
用法：
  python effect_search.py 变身                  # 查变身/觉醒写法
  python effect_search.py 觉醒 形态切换         # 多词叠加
  python effect_search.py 尺度潜降              # 查尺度潜降微世界转场
  python effect_search.py 微世界
  python effect_search.py 变身 --n 3 --full     # 看全文
  python effect_search.py --list                # 列出所有条目标题
"""
import os, sys, re, argparse

sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, '..', 'effect-library.md')

# 查询词 → 召回扩展词（提升命中，不覆盖原词）
SYNONYM = {
    '变身': ['transform', 'transformation', '觉醒', '形态切换', '换装', '神格化', '魔化', '机甲合体', '获神器'],
    '觉醒': ['transform', '变身', 'awaken', '力量爆发', '形态切换'],
    '形态切换': ['transform', '变身', '换装', 'morph'],
    '力量爆发': ['变身', '觉醒', 'burst', 'power surge'],
    '尺度潜降': ['scale dive', 'scale-dive', '微世界', 'macro', '微缩', '无缝转场', '潜入', 'micro'],
    '微世界': ['scale dive', '尺度潜降', 'micro', '微缩文明', 'macro', 'texture-as-world'],
    '转场': ['transition', 'match cut', '尺度潜降', '无缝'],
    '微缩': ['scale dive', '尺度潜降', 'micro', '微世界'],
}


def load_blocks():
    with open(LIB, encoding='utf-8') as f:
        text = f.read()
    lines = text.splitlines()
    blocks = []
    cur_section = ''
    cur = None
    buf = []
    for ln in lines:
        if re.match(r'^##\s', ln):
            if cur is not None:
                blocks.append((cur, '\n'.join(buf)))
                cur = None
            cur_section = ln.lstrip('#').strip()
            buf = []
        elif re.match(r'^###\s', ln):
            if cur is not None:
                blocks.append((cur, '\n'.join(buf)))
            title = ln.lstrip('#').strip()
            cur = (cur_section + ' › ' + title) if cur_section else title
            buf = [title]
        elif re.match(r'^#\s', ln):
            continue
        else:
            if cur is not None:
                buf.append(ln)
    if cur is not None:
        blocks.append((cur, '\n'.join(buf)))
    return blocks


def score(title, body, kws):
    s = 0
    t = title.lower()
    b = body.lower()
    for k in kws:
        kl = k.lower()
        if kl in t:
            s += 100
        s += b.count(kl) * 10
    return s


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument('query', nargs='*', help='中文意图词，如 变身 / 觉醒 / 尺度潜降 / 微世界')
    ap.add_argument('--n', type=int, default=5, help='返回条数')
    ap.add_argument('--full', action='store_true', help='输出条目全文')
    ap.add_argument('--list', action='store_true', help='列出所有条目标题')
    a = ap.parse_args()

    blocks = load_blocks()
    if a.list:
        print('条目清单：')
        for i, (title, _) in enumerate(blocks, 1):
            print(f'  [{i}] {title}')
        return

    kws = []
    for q in a.query:
        kws.append(q)
        kws += SYNONYM.get(q, [])
    kws = list(dict.fromkeys([k for k in kws if k]))

    if not kws:
        print('用法：python effect_search.py 变身 | 尺度潜降 | 微世界 | --list')
        return

    ranked = []
    for title, body in blocks:
        sc = score(title, body, kws)
        if sc > 0:
            ranked.append((sc, title, body))
    ranked.sort(key=lambda x: -x[0])
    ranked = ranked[:a.n]

    if not ranked:
        print('无命中，试试：变身 / 觉醒 / 尺度潜降 / 微世界 / 转场，或 --list 看全部条目。')
        return

    print(f"查询「{' '.join(a.query)}」命中 {len(ranked)} 条：")
    for i, (sc, title, body) in enumerate(ranked, 1):
        print(f"\n{'=' * 60}\n[{i}] {title}  (相关度 {sc})")
        if a.full:
            print(body)
        else:
            lines = [l for l in body.splitlines() if l.strip()]
            preview = lines[:38]
            print('\n'.join(preview))
            if len(lines) > 38:
                print('  ...（--full 看全文）')


if __name__ == '__main__':
    main()
