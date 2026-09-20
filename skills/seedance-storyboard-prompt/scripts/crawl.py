# -*- coding: utf-8 -*-
"""Crawl melies.co/cinematic-techniques: 13 categories -> 424 detail pages -> md + json library."""
import re, os, sys, json, time, html as htmllib
import urllib.request

BASE = 'https://melies.co'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36',
      'Accept-Language': 'en-US,en;q=0.9'}
TMP = r'F:\AI视频制作\outputs\_melies_tmp'
CACHE = os.path.join(TMP, 'cache')
os.makedirs(CACHE, exist_ok=True)

CATS = [
    ('camera-movement', 'Camera Movement', '镜头运动', 86),
    ('framing', 'Framing and Shot Size', '构图与景别', 25),
    ('camera-angles', 'Camera Angles', '镜头角度', 19),
    ('lighting', 'Lighting', '灯光', 41),
    ('composition', 'Composition', '构图', 32),
    ('lenses', 'Lenses and Optics', '镜头与光学', 17),
    ('color', 'Color and Film Look', '色彩与胶片质感', 19),
    ('time-and-motion', 'Time and Motion', '时间与运动', 21),
    ('effects', 'In-Camera and Optical Effects', '机内与光学效果', 57),
    ('editing', 'Editing and Transitions', '剪辑与转场', 23),
    ('atmosphere', 'Atmosphere and Weather', '氛围与天气', 13),
    ('genre-looks', 'Genre Looks', '类型片风格', 27),
    ('viral-looks', 'Viral Looks', '病毒式流行风格', 44),
]

def fetch(url, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            return urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'ignore')
        except Exception as e:
            if i == retries - 1:
                print(f'  FAIL {url} -> {e}')
                return None
            time.sleep(1.5 * (i + 1))

def strip_tags(s):
    s = re.sub(r'<script[\s\S]*?</script>|<style[\s\S]*?</style>', ' ', s)
    s = re.sub(r'<br\s*/?>', '\n', s)
    s = re.sub(r'</(p|li|h[1-6]|div|tr)>', '\n', s)
    s = re.sub(r'<[^>]+>', '', s)
    s = htmllib.unescape(s)
    s = s.replace('\u2019', "'").replace('\u2018', "'").replace('\u201c', '"').replace('\u201d', '"')
    lines = [re.sub(r'\s+', ' ', l).strip() for l in s.split('\n')]
    return [l for l in lines if l]

UI_EXACT = {'Bookmark', 'Close', 'Copy prompt', 'Use in Video Generator', 'Prompt it',
            'Questions', 'Cancel', 'Send report', 'Narrative', 'Mistakes', 'Definition'}
UI_PREFIX = ('Create this', 'Report an issue', 'Tell us if', 'Describe the issue',
             'You can send this', 'What\u2019s inaccurate', "What's inaccurate", 'Filter techniques')

def split_sections(html):
    """Return (title, pre_html, {section_title: section_html})."""
    h1 = re.search(r'<h1[^>]*>([\s\S]*?)</h1>', html)
    title = htmllib.unescape(re.sub(r'<[^>]+>', '', h1.group(1))).strip() if h1 else '?'
    parts = re.split(r'<h2[^>]*>', html)
    pre = parts[0]
    secs = {}
    for p in parts[1:]:
        m = re.match(r'([\s\S]*?)</h2>([\s\S]*?)(?=<h2|$)', p)
        if m:
            t = re.sub(r'<[^>]+>', '', m.group(1)).strip()
            secs[t] = m.group(2)
    return title, pre, secs

def clean_dup(s):
    """If a line is the same text concatenated twice, keep one half."""
    n = len(s)
    if n % 2 == 0 and s[: n // 2] == s[n // 2:]:
        return s[: n // 2]
    return s

def parse_detail(html, cat_slug, all_names=()):
    title, pre, secs = split_sections(html)
    lines = strip_tags(pre)
    # aliases + definition via stable class selectors
    aliases, definition = [], ''
    m_also = re.search(r'<p class="cinematic-sheet__also"[\s\S]*?</p>', html)
    if m_also:
        aliases = [htmllib.unescape(re.sub(r'<[^>]+>', '', t)).strip()
                   for t in re.findall(r'<span class="cinematic-tag"[^>]*>([\s\S]*?)</span>', m_also.group(0))]
        aliases = [a for a in aliases if a]
    m_def = re.search(r'<p id="definition"[^>]*>([\s\S]*?)</p>', html)
    if m_def:
        definition = ' '.join(strip_tags(m_def.group(1)))
    # sections
    def sec_text(name):
        if name not in secs:
            return ''
        return '\n'.join(strip_tags(secs[name]))
    # narrative: paragraphs
    narr_paras = []
    if 'Narrative function' in secs:
        narr_paras = [p for p in '\n'.join(strip_tags(secs['Narrative function'])).split('\n') if p]
    # compared: names from links + text
    comp_names, comp_text = [], []
    if 'Compared with similar shots' in secs:
        c = secs['Compared with similar shots']
        comp_names = [htmllib.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip()
                      for m in re.finditer(r'<a[^>]*>([\s\S]*?)</a>', c)]
        comp_text = [p for p in '\n'.join(strip_tags(c)).split('\n') if p]
    # in film: lines
    film_lines = []
    if 'In film' in secs:
        film_lines = strip_tags(secs['In film'])
    # prompt section
    template, example, note = '', '', ''
    if 'Prompt it' in secs:
        paras = [p for p in '\n'.join(strip_tags(secs['Prompt it'])).split('\n') if p]
        paras = [p for p in paras if p not in UI_EXACT and not any(p.startswith(x) for x in UI_PREFIX)]
        for frag in ('Copy prompt', 'Use in Image Generator', 'Use in Video Generator'):
            paras = [p.replace(frag, '').strip() for p in paras]
        paras = [clean_dup(p) for p in paras if p]
        big = [p for p in paras if len(p) >= 60]
        rest = [p for p in paras if len(p) < 60]
        seen = set()
        uniq = []
        for p in big:
            if p not in seen:
                seen.add(p)
                uniq.append(p)
        if uniq:
            uniq.sort(key=len, reverse=True)
            template = uniq[0]
            if len(uniq) > 1:
                example = uniq[1]
        note = ' / '.join(dict.fromkeys(p for p in rest if p.lower() not in ('close', 'questions')))
    mistakes = ''
    if 'What usually goes wrong' in secs:
        mistakes = '\n'.join(strip_tags(secs['What usually goes wrong']))
    # questions: h3 + following text
    faq = []
    if 'Questions' in secs:
        qparts = re.split(r'<h3[^>]*>', secs['Questions'])
        for qp in qparts[1:]:
            m = re.match(r'([\s\S]*?)</h3>([\s\S]*?)$', qp)
            if m:
                q = re.sub(r'<[^>]+>', '', m.group(1)).strip()
                a = '\n'.join(strip_tags(m.group(2)))
                faq.append((q, a))
    return {
        'name': title,
        'category_slug': cat_slug,
        'aliases': aliases,
        'definition': definition,
        'narrative': narr_paras,
        'how_it_works': sec_text('How it works'),
        'when_to_use': sec_text('When to use it'),
        'compared_names': comp_names,
        'compared_text': comp_text,
        'in_film': film_lines,
        'prompt_template': template,
        'prompt_example': example,
        'prompt_note': note,
        'mistakes': mistakes,
        'faq': faq,
        'url': f'{BASE}/cinematic-techniques/{cat_slug}/'  # filled by caller
    }

def main():
    # 1) collect links from category pages
    items = []  # (cat_slug, slug, name)
    for slug, en, zh, n in CATS:
        html = fetch(f'{BASE}/cinematic-techniques/{slug}')
        if not html:
            print(f'CATEGORY FAIL {slug}')
            continue
        found = []
        for m in re.finditer(r'href="/cinematic-techniques/([a-z0-9-]+)/([a-z0-9-]+)"[^>]*>([\s\S]*?)</a>', html):
            c, s = m.group(1), m.group(2)
            if c != slug:
                continue
            name = re.sub(r'<[^>]+>', '', m.group(3)).strip()
            found.append((c, s, name))
        # dedupe keep order
        seen = set()
        uniq = []
        for it in found:
            if it[1] not in seen:
                seen.add(it[1])
                uniq.append(it)
        print(f'{slug}: {len(uniq)} (expect {n})')
        items.extend(uniq)
    print(f'TOTAL links: {len(items)}')
    json.dump(items, open(os.path.join(TMP, 'links.json'), 'w', encoding='utf-8'), ensure_ascii=False)

    # 2) fetch detail pages (with cache)
    fails = []
    for i, (c, s, name) in enumerate(items):
        path = os.path.join(CACHE, f'{c}__{s}.html')
        if os.path.exists(path) and os.path.getsize(path) > 20000:
            continue
        html = fetch(f'{BASE}/cinematic-techniques/{c}/{s}')
        if html:
            open(path, 'w', encoding='utf-8').write(html)
        else:
            fails.append((c, s))
        if (i + 1) % 25 == 0:
            print(f'fetched {i+1}/{len(items)}')
        time.sleep(0.25)
    print(f'DONE fetching, fails={len(fails)}: {fails[:10]}')

    # 3) parse all cached pages
    name_set = {name for _, _, name in items}
    records = []
    for c, s, name in items:
        path = os.path.join(CACHE, f'{c}__{s}.html')
        if not os.path.exists(path):
            continue
        html = open(path, encoding='utf-8').read()
        rec = parse_detail(html, c, name_set)
        rec['slug'] = s
        rec['url'] = f'{BASE}/cinematic-techniques/{c}/{s}'
        records.append(rec)
    print(f'parsed: {len(records)}')
    json.dump(records, open(os.path.join(TMP, 'techniques.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    empty_def = [r['name'] for r in records if not r['definition']]
    no_prompt = [r['name'] for r in records if not r['prompt_template']]
    print(f'empty definition: {len(empty_def)} {empty_def[:8]}')
    print(f'empty prompt: {len(no_prompt)} {no_prompt[:8]}')

if __name__ == '__main__':
    main()
