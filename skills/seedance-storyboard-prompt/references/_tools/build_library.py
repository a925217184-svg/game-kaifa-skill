# -*- coding: utf-8 -*-
"""Build the skill reference library from crawled techniques.json."""
import json, os, re

TMP = r'F:\AI视频制作\outputs\_melies_tmp'
SKILL_REF = r'C:\Users\Administrator\.workbuddy\skills\seedance-storyboard-prompt\references'
os.makedirs(SKILL_REF, exist_ok=True)

CATS = {
    'camera-movement': ('Camera Movement', '镜头运动'),
    'framing': ('Framing and Shot Size', '构图与景别'),
    'camera-angles': ('Camera Angles', '镜头角度'),
    'lighting': ('Lighting', '灯光'),
    'composition': ('Composition', '构图'),
    'lenses': ('Lenses and Optics', '镜头与光学'),
    'color': ('Color and Film Look', '色彩与胶片质感'),
    'time-and-motion': ('Time and Motion', '时间与运动'),
    'effects': ('In-Camera and Optical Effects', '机内与光学效果'),
    'editing': ('Editing and Transitions', '剪辑与转场'),
    'atmosphere': ('Atmosphere and Weather', '氛围与天气'),
    'genre-looks': ('Genre Looks', '类型片风格'),
    'viral-looks': ('Viral Looks', '病毒式流行风格'),
}

records = json.load(open(os.path.join(TMP, 'techniques.json'), encoding='utf-8'))
# group by category, keep original order
by_cat = {}
for r in records:
    by_cat.setdefault(r['category_slug'], []).append(r)

md = []
md.append('# 电影技巧技术库（Cinematic Techniques Library）v1.0')
md.append('')
md.append('> 来源：https://melies.co/cinematic-techniques （全站 424 条技巧，2026-09-20 抓取）')
md.append('> 用途：`seedance-storyboard-prompt` 技能的选型词典。写分镜/提示词时，镜头运动、景别、角度、灯光、构图、焦段、色彩、时间处理、机内特效、转场、氛围天气、类型风格一律**先查本库再落笔**；词条正文为英文原文（Prompt 模板可直接用），引用到脚本时由 AI 翻译/本地化。')
md.append('> 检索方式：按分类 Ctrl+F，或告诉 AI 需求让它从库里挑 3–5 个候选。')
md.append('')
md.append('## 目录（13 类 / %d 条）' % len(records))
md.append('')
md.append('| 分类 | 条数 | 分类 | 条数 |')
md.append('|---|---|---|---|')
cats_list = [(k, *CATS[k], len(by_cat.get(k, []))) for k in CATS]
for i in range(0, len(cats_list), 2):
    row = cats_list[i:i + 2]
    cells = []
    for k, en, zh, n in row:
        cells.append(f'{zh} {en} | {n}')
    while len(cells) < 2:
        cells.append('— | —')
    md.append('| ' + ' | '.join(cells) + ' |')
md.append('')
md.append('---')
md.append('')

for k in CATS:
    en, zh = CATS[k]
    items = by_cat.get(k, [])
    if not items:
        continue
    md.append(f'## {zh} / {en}（{len(items)} 条）')
    md.append('')
    # quick index
    md.append('**速查**：' + ' · '.join(r['name'] for r in items))
    md.append('')
    for r in items:
        md.append(f"### {r['name']}")
        meta = []
        if r['aliases']:
            meta.append('别名：' + ', '.join(r['aliases'][:6]))
        meta.append(f"[原文]({r['url']})")
        md.append('- ' + ' ｜ '.join(meta))
        if r['definition']:
            md.append(f"- 定义：{r['definition']}")
        if r['narrative']:
            md.append('- 叙事功能：' + ' '.join(r['narrative']))
        if r['how_it_works']:
            md.append('- 怎么拍：' + r['how_it_works'].replace('\n', ' '))
        if r['when_to_use']:
            md.append('- 何时用：' + r['when_to_use'].replace('\n', ' '))
        if r['compared_names']:
            md.append('- 近似对比：' + ', '.join(dict.fromkeys(r['compared_names'])))
            body = ' '.join(r['compared_text'])
            if body:
                md.append('  ' + body)
        if r['in_film']:
            film = '；'.join(r['in_film'][:6])
            md.append(f'- 片中实例：{film}')
        if r['prompt_template']:
            md.append(f"- Prompt 模板：`{r['prompt_template']}`")
        if r['prompt_example']:
            md.append(f"- 示例 Prompt：`{r['prompt_example']}`")
        if r['prompt_note']:
            md.append(f"- Prompt 要点：{r['prompt_note']}")
        if r['mistakes']:
            md.append('- 常见错误：' + r['mistakes'].replace('\n', ' '))
        md.append('')

md_path = os.path.join(SKILL_REF, 'cinematic-techniques.md')
open(md_path, 'w', encoding='utf-8').write('\n'.join(md))
print('md written:', md_path, len('\n'.join(md)), 'chars')

json_path = os.path.join(SKILL_REF, 'cinematic-techniques.json')
json.dump(records, open(json_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('json written:', json_path, len(records), 'records')
