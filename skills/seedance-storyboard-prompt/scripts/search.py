#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
电影技巧库检索工具（melies.co 424 条）
用法：
  python search.py 压迫感                # 中文意图词（内置映射）
  python search.py "压迫感 夜戏"          # 多词叠加
  python search.py --en "slow zoom"      # 英文关键词
  python search.py --en backlight --cat lighting
  python search.py --intent              # 列出所有内置中文意图词
  python search.py --en "dolly" --n 3 --full
  python search.py --name "Rembrandt Lighting"   # 精确取一条全文
"""
import json, os, sys, re, argparse

sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

HERE = os.path.dirname(os.path.abspath(__file__))
JSON = os.path.join(HERE, '..', 'cinematic-techniques.json')

# 中文意图 → (英文检索词, 推荐候选词条名)
INTENT = {
    # —— 情绪/氛围 ——
    '压迫感': (['pressure', 'menace', 'looming', 'oppressive', 'threat'], ['Slow Zoom In', 'Push In', 'Low Angle', 'Worm\'s-Eye View', 'Chiaroscuro', 'Telephoto Compression']),
    '紧张': (['tension', 'suspense', 'anxious', 'edgy'], ['Dutch Angle', 'Handheld', 'Slow Zoom In', 'Rack Focus', 'Low-Key Lighting', 'Quick Cuts']),
    '爽感': (['satisfying', 'reward', 'payoff', 'triumph'], ['Crash Zoom In', 'Whip Pan', 'Speed Ramp', 'Slow Motion', 'Hero Cam', 'Bokeh']),
    '燃': (['epic', 'heroic', 'energy', 'hype'], ['Low Angle', 'Crane Up', 'Orbit', 'Motion Blur', 'Sparks and Embers', 'Slow Motion', 'Halation']),
    '反转': (['reveal', 'twist', 'reversal', 'turn'], ['Crash Zoom In', 'Dolly Zoom', 'Smash Cut', 'Focus Change', 'Reverse Angle', 'Epiphany']),
    '悬念': (['suspense', 'mystery', 'withheld', 'reveal'], ['Slow Zoom In', 'Dirty Frame', 'Voyeur', 'Silhouette', 'Low-Key Lighting', 'Rack Focus']),
    '震惊': (['shock', 'astonish', 'stun'], ['Crash Zoom In', 'Smash Cut', 'Freeze Frame', 'Dolly Zoom', 'Flash Cut', 'Extreme Close-Up (ECU)']),
    '孤独': (['lonely', 'isolation', 'solitude', 'alone'], ['Negative Space', 'Extreme Long Shot (ELS)', 'Wide Shot (WS)', 'High Angle', 'Cool Blue', 'Desaturation']),
    '宏大': (['epic', 'scale', 'vast', 'grandeur'], ['Extreme Long Shot (ELS)', 'Crane Up', 'Aerial', 'Establishing Shot', 'One-Point Perspective', 'Symmetry']),
    '壮观': (['sweeping', 'monumental', 'vista'], ['Aerial', 'Crane Over', 'Hyperlapse', 'Timelapse Landscape', 'Wide Shot (WS)']),
    '亲密': (['intimate', 'closeness', 'tender'], ['Close-Up (CU)', 'Shallow Focus', '85mm Portrait', 'Soft Light', 'Two-Shot', 'Warm Amber']),
    '温情': (['warm', 'tender', 'cozy', 'heartfelt'], ['Warm Amber', 'Candlelight', 'Golden Hour', 'Soft Light', 'Bokeh', 'Practical Lighting']),
    '悲伤': (['sad', 'grief', 'sorrow', 'melancholy'], ['Cool Blue', 'Desaturation', 'Rain', 'Slow Motion', 'High Angle', 'Cameo Lighting']),
    '恐惧': (['fear', 'horror', 'dread', 'terror'], ['Underlighting', 'Dutch Angle', 'Chiaroscuro', 'Low-Key Lighting', 'Handheld', 'Night Vision', 'Cosmic Horror', 'Film Noir']),
    '慌张': (['panic', 'frantic', 'chaos'], ['Handheld', 'Whip Pan', 'Dutch Angle', 'Quick Cuts', 'Stutter / Stop-Stutter', 'Jump Cut']),
    '得意': (['smug', 'triumphant', 'confident', 'proud'], ['Low Angle', 'Hero Cam', 'Slow Motion', 'Bokeh', 'Three-Quarter Angle']),
    '嘲讽': (['sarcastic', 'mocking', 'scorn'], ['Close-Up (CU)', 'Profile', 'Short Lighting', 'Dutch Angle']),
    '威严': (['authority', 'power', 'majestic', 'commanding'], ['Low Angle', 'Worm\'s-Eye View', 'Symmetry', 'Centered Composition', 'Top Light', 'Rembrandt Lighting']),
    '神秘': (['mysterious', 'enigmatic', 'secret'], ['Silhouette', 'Backlight', 'Fog', 'Cameo Lighting', 'Voyeur', 'Volumetric Light']),
    '浪漫': (['romantic', 'longing', 'yearning'], ['Golden Hour', 'Bokeh', 'Soft Light', 'Halation', 'Two-Shot', 'Warm Amber']),

    # —— 场面/动作 ——
    '打斗': (['fight', 'combat', 'brawl'], ['Handheld', 'Speed Ramp', 'Slow Motion', 'Match on Action', 'Close-Up (CU)', 'Sparks and Embers', 'Bullet Time']),
    '追击': (['chase', 'pursuit', 'run'], ['Tracking Shot', 'Steadicam', 'FPV Drone', 'Whip Pan', 'Speed Ramp', 'Parallax', 'Car Chasing']),
    '出场': (['entrance', 'reveal character', 'introduce'], ['Low Angle', 'Crane Up', 'Dolly In', 'Silhouette', 'Push In', 'Rim Light', 'Hero Cam']),
    '登场': (['debut', 'entrance', 'arrival'], ['Crane Up', 'Low Angle', 'Dolly In', 'Slow Motion', 'Backlight', 'Sparks and Embers']),
    '高潮': (['climax', 'peak', 'crescendo'], ['Crane Up', 'Orbit', 'Slow Motion', 'Speed Ramp', 'Montage', 'Low Angle', 'Fire']),
    '落版': (['final frame', 'end card', 'lock off', 'freeze'], ['Freeze Frame', 'Crane Up', 'Aerial Pullback', 'Symmetry', 'Static Locked-Off', 'Vignette']),
    '爆炸': (['explosion', 'blast', 'fire'], ['Sparks and Embers', 'Smoke', 'Slow Motion', 'Light Flash', 'Fire', 'Particles']),
    '战争': (['war', 'battle', 'battlefield'], ['Long Take', 'Handheld', 'Desaturation', 'Dust and Sand', 'Smoke', 'Wide Shot (WS)', 'Oner']),
    '速度感': (['speed', 'fast', 'velocity'], ['Motion Blur', 'Speed Ramp', 'Low Shutter', 'Whip Pan', 'Tracking Shot', 'Timelapse Human']),
    '混乱': (['chaos', 'messy', 'disorder'], ['Handheld', 'Dutch Angle', 'Quick Cuts', 'Dirty Frame', 'Stutter / Stop-Stutter', 'Asymmetry']),

    # —— 时间/叙事 ——
    '时间流逝': (['passage of time', 'time passing', 'years'], ['Time-Lapse', 'Hyperlapse', 'Dissolve', 'Montage', 'Timelapse Landscape']),
    '回忆': (['memory', 'flashback', 'recall'], ['Dissolve', 'Soft Light', 'Filmic Faded', 'Vintage', 'Sepia', 'Bokeh']),
    '闪回': (['flashback', 'cut back'], ['Flash Cut', 'Smash Cut', 'Dissolve', 'Desaturation', 'Sepia', 'Jump Cut']),
    '梦境': (['dream', 'surreal', 'oneiric'], ['Dreamcore', 'Double Exposure', 'Morph', 'Soft Light', 'Halation', 'Weirdcore', 'Slow Motion']),
    '幻觉': (['hallucination', 'delirium', 'altered'], ['Altered State', 'Datamosh', 'Chromatic Aberration', 'Kaleidoscope', 'Double Exposure', 'LSD', 'Thermal']),
    '一镜到底': (['long take', 'oner', 'continuous'], ['Long Take', 'Oner', 'Steadicam', 'Invisible Cut', 'Match on Action']),
    '转场': (['transition', 'cut', 'bridge'], ['Match Cut', 'Whip Pan', 'Invisible Cut', 'Graphic Match', 'Dissolve', 'Wipe', 'Smash Cut']),

    # —— 光线/色彩 ——
    '夜戏': (['night', 'nighttime', 'dark'], ['Low-Key Lighting', 'Blue Hour', 'Moonlight Gel', 'Practical Lighting', 'Silhouette', 'Day for Night', 'Neon Practicals']),
    '白天': (['daylight', 'day', 'sunlit'], ['High-Key Lighting', 'Naturalistic Ambient', 'Bounce Light', 'Golden Hour', 'Available Light']),
    '黄金时刻': (['golden hour', 'sunset', 'magic hour'], ['Golden Hour', 'Backlight', 'Lens Flare', 'Halation', 'Warm Amber', 'Long Shot (WS)']),
    '火光': (['firelight', 'fire', 'flame', 'ember'], ['Practical Lighting', 'Sparks and Embers', 'Underlighting', 'Warm Amber', 'Chiaroscuro', 'Motivated Lighting']),
    '冷暖对比': (['warm cool contrast', 'color contrast', 'teal orange'], ['Teal and Orange', 'Split Toning', 'Cross Lighting', 'Tonal Contrast', 'Motivated Lighting']),
    '烛光': (['candle', 'candlelight', 'lantern'], ['Candlelight', 'Practical Lighting', 'Chiaroscuro', 'Warm Amber', 'Eye Light']),
    '室内光': (['interior light', 'indoor', 'room light'], ['Window Light', 'Practical Lighting', 'Three-Point Lighting', 'Bounce Light', 'Naturalistic Ambient']),
    '天气': (['weather', 'atmosphere'], ['Fog', 'Rain', 'Snow', 'Mist', 'Smoke', 'Atmospheric Haze', 'Dust Motes', 'Steam', 'Ocean']),
    '火把': (['torch', 'firelight', 'flame'], ['Practical Lighting', 'Sparks and Embers', 'Underlighting', 'Warm Amber', 'Motivated Lighting']),
    '油灯': (['oil lamp', 'lantern', 'candlelight'], ['Practical Lighting', 'Candlelight', 'Chiaroscuro', 'Warm Amber', 'Eye Light']),
    '军帐': (['tent interior', 'warm interior', 'lantern'], ['Practical Lighting', 'Candlelight', 'Chiaroscuro', 'Motivated Lighting', 'Eye Light']),
    '逆光': (['backlight', 'backlit', 'against the light'], ['Backlight', 'Silhouette', 'Lens Flare', 'Halation', 'Rim Light', 'Golden Hour']),
    '剪影': (['silhouette', 'dark shape', 'rim'], ['Silhouette', 'Backlight', 'Rim Light', 'Cameo Lighting', 'Low-Key Lighting']),
    '轮廓光': (['rim light', 'edge light', 'kicker'], ['Rim Light', 'Backlight', 'Three-Point Lighting', 'Cameo Lighting']),
    '顶光': (['top light', 'overhead light'], ['Top Light', 'Chiaroscuro', 'Rembrandt Lighting', 'Hard Light']),
    '底光': (['underlighting', 'light from below'], ['Underlighting', 'Horror', 'Chiaroscuro', 'Eerie']),
    '眼神光': (['catchlight', 'eye light'], ['Eye Light', 'Close-Up (CU)', 'Three-Point Lighting', 'Soft Light']),
    '体积光': (['volumetric', 'god rays', 'light beam'], ['Volumetric Light', 'Atmospheric Haze', 'Dust Motes', 'Fog', 'Steam']),
    '丁达尔': (['tyndall', 'god rays', 'light shaft'], ['Volumetric Light', 'Dust Motes', 'Fog', 'Window Light']),
    '雾': (['fog', 'mist', 'haze'], ['Fog', 'Mist', 'Atmospheric Haze', 'Volumetric Light', 'Silhouette']),
    '雨': (['rain', 'wet', 'storm'], ['Rain', 'Storm', 'Cool Blue', 'Desaturation', 'Slow Motion']),
    '雪': (['snow', 'winter', 'cold'], ['Snow', 'Cool Blue', 'High-Key Lighting', 'Desaturation']),
    '沙尘': (['dust', 'sand', 'particle'], ['Dust and Sand', 'Dust Motes', 'Smoke', 'Atmospheric Haze', 'Desaturation']),
    '冷暖': (['warm cool', 'teal orange', 'color contrast'], ['Teal and Orange', 'Split Toning', 'Cross Lighting', 'Tonal Contrast']),
    '色调': (['color grade', 'tonal', 'palette'], ['Teal and Orange', 'Split Toning', 'Desaturation', 'Cool Blue', 'Warm Amber']),
    '俯拍': (['overhead', 'high angle', 'top down', 'aerial'], ['High Angle', 'Aerial', "Bird's-Eye View", 'Crane Over', 'Establishing Shot']),
    '仰拍': (['low angle', 'looking up', 'worm'], ['Low Angle', "Worm's-Eye View", 'Hero Cam', 'Crane Up']),
    '特写': (['close up', 'extreme close up', 'detail'], ['Close-Up (CU)', 'Extreme Close-Up (ECU)', 'Insert', 'Shallow Focus', 'Macro']),
    '跟拍': (['tracking', 'follow', 'steadicam'], ['Tracking Shot', 'Steadicam', 'Parallax', 'Long Take', 'Dolly']),
    '环绕': (['orbit', 'around', 'arc'], ['Orbit', 'Arc', 'Crane Over', 'Bullet Time', 'Steadicam']),
    '慢动作': (['slow motion', 'slowmo', 'ramp'], ['Slow Motion', 'Speed Ramp', 'Bullet Time', 'Overcrank']),
    '定格': (['freeze', 'lock off', 'still'], ['Freeze Frame', 'Static Locked-Off', 'Vignette', 'Symmetry']),
    '推近': (['push in', 'dolly in', 'zoom in'], ['Push In', 'Dolly In', 'Slow Zoom In', 'Crash Zoom In']),
    '拉远': (['pull back', 'pull out', 'widen'], ['Pull Back', 'Aerial Pullback', 'Crane Up', 'Wide Shot (WS)']),
    '横移': (['lateral', 'pan', 'slide', 'truck'], ['Pan', 'Tracking Shot', 'Whip Pan', 'Dolly']),
    '手持': (['handheld', 'shaky', 'documentary'], ['Handheld', 'Shaky Cam', 'Found Footage', 'Dutch Angle']),
    '第一人称': (['first person', 'pov', 'subjective'], ['POV', 'FPV Drone', 'Handheld', 'Voyeur', 'Over the Shoulder']),
    '对峙': (['standoff', 'confrontation', 'face off'], ['Split Screen', 'Short Lighting', 'Cross Lighting', 'Two-Shot', 'Symmetry', 'Telephoto Compression']),
    '对话': (['dialogue', 'conversation', 'two shot'], ['Two-Shot', 'Over the Shoulder', 'Shot Reverse Shot', 'Shallow Focus']),
    '群像': (['group', 'ensemble', 'crowd'], ['Wide Shot (WS)', 'Deep Focus', 'Symmetry', 'Blocking', 'Establishing Shot']),
    '大场面': (['spectacle', 'massive', 'army'], ['Extreme Long Shot (ELS)', 'Aerial', 'Crane Up', 'One-Point Perspective', 'Symmetry']),
    '弹窗': (['floating ui', 'hud', 'interface'], ['Floating UI', 'Tech Noir', 'Random Glow', 'Blue Depth', 'Hologram']),
    '暖光': (['warm light', 'warm amber', 'warm interior'], ['Warm Amber', 'Candlelight', 'Practical Lighting', 'Golden Hour', 'Soft Light']),
    '冷光': (['cool light', 'cool blue', 'cold'], ['Cool Blue', 'Moonlight Gel', 'Blue Hour', 'Low-Key Lighting', 'Night Vision']),
    '月光': (['moonlight', 'moon', 'night sky'], ['Moonlight Gel', 'Blue Hour', 'Low-Key Lighting', 'Silhouette', 'Day for Night']),
    '日光': (['daylight', 'sunlight', 'sun'], ['High-Key Lighting', 'Naturalistic Ambient', 'Available Light', 'Golden Hour', 'Bounce Light']),
    '内景': (['interior', 'indoor', 'inside'], ['Practical Lighting', 'Window Light', 'Three-Point Lighting', 'Motivated Lighting', 'Chiaroscuro']),
    '外景': (['exterior', 'outdoor', 'outside'], ['Available Light', 'Naturalistic Ambient', 'Golden Hour', 'Blue Hour', 'Establishing Shot']),
    '火攻': (['fire', 'flame', 'burning', 'blaze'], ['Fire', 'Sparks and Embers', 'Smoke', 'Light Flash', 'Underlighting', 'Chiaroscuro']),
    '战场': (['battlefield', 'war', 'battle'], ['Long Take', 'Handheld', 'Dust and Sand', 'Smoke', 'Desaturation', 'Wide Shot (WS)']),
    '城楼': (['castle', 'rampart', 'fortress', 'city wall'], ['Establishing Shot', 'Low Angle', 'Aerial', 'One-Point Perspective', 'Symmetry']),
    '爆炸火光': (['explosion', 'blast', 'fireball'], ['Light Flash', 'Fire', 'Sparks and Embers', 'Smoke', 'Slow Motion', 'Particles']),
    '机甲': (['mecha', 'robot', 'armor'], ['Low Angle', "Worm's-Eye View", 'Sparks and Embers', 'Smoke', 'Light Flash', 'Blockbuster Gloss']),

    # —— 风格 ——
    '国风': (['chinese', 'oriental', 'wuxia', 'ink'], ['Wuxia', 'Ink Riot', 'Hand Paint', 'Paper', 'Origami', 'Fairytale Castle', 'Golden Ratio', 'Symmetry']),
    '武侠': (['wuxia', 'martial arts', 'swordplay'], ['Wuxia', 'Slow Motion', 'Wire', 'Crane Up', 'Sparks and Embers', 'Mist']),
    '科技感': (['tech', 'sci-fi', 'futuristic'], ['Tech Noir', 'Floating UI', 'Neon Practicals', 'Volumetric Light', 'Cool Blue', 'Hologram', 'Random Glow', 'Blue Depth']),
    '赛博朋克': (['cyberpunk', 'neon', 'dystopian'], ['Neon Practicals', 'Tech Noir', 'Dystopian', 'Cool Blue', 'Volumetric Light', 'Night Vision', 'Ultraviolet']),
    '复古': (['vintage', 'retro', 'nostalgic'], ['Vintage', 'Sepia', 'Filmic Faded', 'Film Grain', 'Halation', 'Vintage Cine Glass', '2000s Paparazzi']),
    '胶片感': (['film look', 'grain', 'analog'], ['Film Grain', 'Halation', 'Vintage', 'Bleach Bypass', 'Cross Process', 'Filmic Faded', 'Anamorphic']),
    '高级感': (['premium', 'elegant', 'luxury', 'polished'], ['Soft Light', 'Glam', 'Bokeh', 'Shallow Focus', 'Teal and Orange', 'Anamorphic', 'Symmetry']),
    '电影感': (['cinematic', 'film look'], ['Anamorphic', 'Shallow Focus', 'Lens Flare', 'Teal and Orange', 'Film Grain', 'Letterbox', 'Halation']),
    '游戏感': (['game', 'videogame', 'cg'], ['Video Game', '3D Render', 'Floating UI', 'Photogrammetry', 'Blockbuster Gloss', 'Diorama']),
    '动画': (['animation', 'cartoon', 'anime'], ['Animation', 'Comic', 'Flash Comic', 'Pixel Art', 'Hand Paint', 'Paper', 'Stylistic Suck']),
}

CAT_CN = {
    'camera-movement': '镜头运动', 'effects': '机内特效', 'viral-looks': '病毒风格', 'lighting': '灯光',
    'composition': '构图', 'genre-looks': '类型风格', 'framing': '构图景别', 'editing': '剪辑转场',
    'time-and-motion': '时间运动', 'camera-angles': '镜头角度', 'color': '色彩胶片', 'lenses': '镜头光学',
    'atmosphere': '氛围天气',
}


def load():
    with open(JSON, encoding='utf-8') as f:
        return json.load(f)


def score(rec, kws, seeds):
    s = 0
    name_l = rec['name'].lower()
    for n in seeds:
        if n.lower() == name_l:
            s += 200
    for k in kws:
        k = k.lower()
        if k == name_l:
            s += 120
        elif k in name_l:
            s += 60
        if any(k in a.lower() for a in rec.get('aliases') or []):
            s += 30
        blob = ' '.join([
            rec.get('definition') or '',
            ' '.join(rec.get('narrative') or []),
            rec.get('when_to_use') or '',
            rec.get('how_it_works') or '',
        ]).lower()
        if k in blob:
            s += 12
        if rec.get('prompt_template') and k in rec['prompt_template'].lower():
            s += 8
    return s


def show(r, i, full=False):
    print(f"\n[{i}] {r['name']}  ·  {CAT_CN.get(r['category_slug'], r['category_slug'])}")
    print(f"    定义: {(r.get('definition') or '')[:190]}")
    nar = r.get('narrative') or []
    if nar:
        print(f"    功能: {nar[0][:170]}")
    if r.get('prompt_template'):
        print(f"    模板: {r['prompt_template'][:340]}")
    if full:
        if len(nar) > 1:
            for n in nar[1:]:
                print(f"          + {n[:160]}")
        for k, label in [('how_it_works', '怎么拍'), ('when_to_use', '何时用'), ('mistakes', '常见错误')]:
            if r.get(k):
                print(f"    {label}: {r[k][:300]}")
        if r.get('prompt_example'):
            print(f"    示例: {r['prompt_example'][:280]}")
        if r.get('in_film'):
            print(f"    片例: {r['in_film'][:180]}")
    print(f"    原文: {r.get('url')}")


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument('query', nargs='*', help='中文意图词或英文关键词')
    ap.add_argument('--en', action='append', default=[], help='英文关键词（可多次）')
    ap.add_argument('--cat', default=None, help='限定分类 slug，如 lighting')
    ap.add_argument('--n', type=int, default=6, help='返回条数')
    ap.add_argument('--full', action='store_true', help='输出全字段')
    ap.add_argument('--name', default=None, help='按名称精确取一条全文')
    ap.add_argument('--intent', action='store_true', help='列出内置中文意图词')
    a = ap.parse_args()

    data = load()

    if a.intent:
        print('内置中文意图词（可直接作为 query）：')
        ks = list(INTENT.keys())
        for i in range(0, len(ks), 6):
            print('  ' + ' · '.join(ks[i:i + 6]))
        return

    if a.name:
        for r in data:
            if r['name'].lower() == a.name.lower():
                show(r, 1, full=True)
                return
        print('未找到：', a.name)
        return

    kws, seeds = [], []
    unknown = []
    for q in a.query + a.en:
        if q in INTENT:
            k, s = INTENT[q]
            kws += k
            seeds += s
            continue
        # 子串匹配：查询词里含有某个意图词（如「夜戏火光」含「火光」）或意图词含查询词
        hit = [key for key in INTENT if (key in q and len(key) >= 2) or (len(q) >= 2 and q in key)]
        if hit:
            for key in hit:
                k, s = INTENT[key]
                kws += k
                seeds += s
        else:
            kws.append(q)
            if re.search(r'[\u4e00-\u9fff]', q):
                unknown.append(q)
    if not kws and not seeds:
        print('用法：python search.py 压迫感 | --en "slow zoom" | --name "Rembrandt Lighting" | --intent')
        return

    if unknown:
        print('（未在内置意图表中，已按字面检索：' + '、'.join(unknown) + '）')

    pool = [r for r in data if not a.cat or r['category_slug'] == a.cat]
    ranked = sorted(((score(r, set(kws), set(seeds)), r) for r in pool), key=lambda x: -x[0])
    ranked = [x for x in ranked if x[0] > 0][:a.n]

    if not ranked:
        print('无命中，试试 --intent 看内置词，或换英文关键词。')
        return

    label = ' '.join(a.query + a.en)
    print(f"查询「{label}」命中 {len(ranked)} 条：")
    for i, (s, r) in enumerate(ranked, 1):
        show(r, i, full=a.full)


if __name__ == '__main__':
    main()
