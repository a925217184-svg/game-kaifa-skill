# -*- coding: utf-8 -*-
"""
把本地真源（规范 / 表情库 / 424 条技巧库 / 意图映射表 / 实战示例）
组装成一份「自包含、可发给豆包 Gemini 等网页 AI」的规范包。

用法：cd web-ai-pack && python _source/build_pack.py
输出：包根目录下 00_怎么用.md / 01_开场指令.txt / 02_网页AI规范_完整自包含版.md / 02b_网页AI规范_轻量版.md / 03_技巧库_全量424条.md
仓库版路径全部相对仓库根，clone 下来即可原地重跑。
"""
import io, os, json, re, textwrap

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # web-ai-pack/
REPO = os.path.dirname(ROOT)                                          # 仓库根
SKILL = os.path.join(REPO, "skills", "seedance-storyboard-prompt")

SRC_MAIN = os.path.join(ROOT, "_source", "主体模板.md")
EXPR_LIB = os.path.join(SKILL, "references", "expression-library.md")
INTENT_MAP = os.path.join(SKILL, "references", "intent-to-technique.md")
TECH_JSON = os.path.join(SKILL, "references", "cinematic-techniques.json")
EXAMPLE = os.path.join(ROOT, "_source", "示例_风云助阵_v2.txt")

CAT_CN = {
    "camera-movement": "镜头运动", "camera-angles": "机位角度", "framing": "构图景别",
    "composition": "构图", "lenses": "镜头光学", "lighting": "灯光", "color": "色彩胶片",
    "time-and-motion": "时间运动", "effects": "机内特效", "editing": "剪辑转场",
    "atmosphere": "氛围天气", "genre-looks": "类型风格", "viral-looks": "病毒风格",
}
CAT_ORDER = ["camera-movement", "camera-angles", "framing", "composition", "lenses",
             "lighting", "color", "time-and-motion", "effects", "editing",
             "atmosphere", "genre-looks", "viral-looks"]


def read(p):
    return io.open(p, encoding="utf-8").read()


def first_sentences(text, n=2, limit=300):
    if not text:
        return ""
    if isinstance(text, list):
        text = " ".join(str(x) for x in text)
    text = " ".join(str(text).split())
    parts = re.split(r"(?<=[.!?])\s+", text)
    out = " ".join(parts[:n])
    return out[:limit] + ("…" if len(out) > limit else "")


def card_lite(item, idx):
    """轻量版：一行一条，只留定义 + 避坑，不输出 Prompt 模板"""
    name = item.get("name", "")
    cat = CAT_CN.get(item.get("category_slug", ""), item.get("category_slug", ""))
    d = first_sentences(item.get("definition"), 1, 130)
    mis = first_sentences(item.get("mistakes"), 1, 90)
    s = "- **%s**｜%s｜%s" % (name, cat, d)
    if mis:
        s += "｜避坑：%s" % mis
    return s


def card(item, idx):
    name = item.get("name", "")
    cat = CAT_CN.get(item.get("category_slug", ""), item.get("category_slug", ""))
    d = first_sentences(item.get("definition"), 2, 280)
    tpl = first_sentences(item.get("prompt_template"), 6, 420)
    mis = first_sentences(item.get("mistakes"), 2, 180)
    lines = ["**%d. %s**（%s）" % (idx, name, cat)]
    if d:
        lines.append("- 定义：%s" % d)
    if tpl:
        lines.append("- Prompt 模板：%s" % tpl)
    if mis:
        lines.append("- 避坑：%s" % mis)
    return "\n".join(lines)


def example_note(raw):
    """从示例的说明区抽出可示范的小节（技巧依据 / 字数自检），剔除本地路径与文件引用。

    目的：让网页 AI 看到「说明区该长什么样」，尤其是字数自检表必须出现在交付里。
    """
    if "以下为说明区" not in raw:
        return ""
    note = raw.split("以下为说明区", 1)[1]
    blocks = re.split(r"\n(?=【)", note)
    keep = [b.strip() for b in blocks
            if b.strip().startswith("【技巧依据】") or b.strip().startswith("【字数自检】")]
    if not keep:
        return ""
    cleaned = []
    for b in keep:
        lines = [l for l in b.split("\n")
                 if not re.search(r"[A-Za-z]:\\\\|\\\\Users\\\\|clipboard-images|\\\\.mp3|\\\\.MP3", l)]
        blk = "\n".join(lines).strip()
        blk = blk.replace("（工具 count_chars.py）", "（逐字数统计，去空白）")
        cleaned.append(blk)
    body = "\n\n".join(cleaned)
    return ("———— 以下为【说明区】节选（示范核对信息该怎么写，一律不复制进 Seedance） ————\n\n"
            + body + "\n\n> 完整说明区还应有：参考图挂载 / 执行参数 / 口播对齐 / 备注 / 自检清单。")


def build():
    tech = json.loads(read(TECH_JSON))
    intent_text = read(INTENT_MAP)
    hot = [x for x in tech if x["name"] in intent_text]          # 映射表命中 = 高频
    hot.sort(key=lambda x: (CAT_ORDER.index(x["category_slug"]) if x["category_slug"] in CAT_ORDER else 99))

    # 分类索引（424 条全量）
    idx_lines = []
    for c in CAT_ORDER:
        names = [x["name"] for x in tech if x["category_slug"] == c]
        if names:
            idx_lines.append("- **%s（%d 条）**：%s" % (CAT_CN[c], len(names), "、".join(names)))
    tech_index = "\n".join(idx_lines)

    # 高频词条卡
    cards = [card(x, i + 1) for i, x in enumerate(hot)]
    tech_cards = "\n\n".join(cards)

    # 表情库（截到「六、分角色推荐词条」之前，去掉本地路径与校准记录）
    expr = read(EXPR_LIB)
    expr = expr.split("## 六、分角色推荐词条")[0]
    expr = expr.split("## 〇、通用规则", 1)[1]
    expr = "## 〇、通用规则" + expr
    expr = expr.strip()

    # 意图映射表（去掉检索脚本命令行）
    intent = read(INTENT_MAP)
    intent = re.sub(r"^>.*search\.py.*$", "", intent, flags=re.M)
    intent = intent.split("## 使用原则", 1)[1]
    intent = "## 使用原则" + intent
    intent = re.sub(r"\n{3,}", "\n\n", intent).strip()

    # 示例（可复制区 + 说明区节选）
    raw = read(EXAMPLE)
    ex = raw
    if "以下为说明区" in ex:
        ex = ex.split("以下为说明区")[0].rstrip()
    ex = ex.replace("【全局锁】（全文仅此一处，复制时带上本段 + 目标 Shot 正文）", "【全局锁】")
    ex = ex.rstrip()
    ex_note = example_note(raw)
    if ex_note:
        ex = ex + "\n\n---\n\n" + ex_note

    # 02b 轻量版：词条卡换成一行式
    lite = (read(SRC_MAIN)
            .replace("<<TECH_CARDS>>", "\n".join(card_lite(x, i + 1) for i, x in enumerate(hot)))
            .replace("<<EXPRESSION_LIB>>", expr))
    lite = (lite.replace("<<INTENT_MAP>>", intent)
                .replace("<<TECH_INDEX>>", "\n".join(idx_lines))
                .replace("<<EXAMPLE>>", ex))
    io.open(os.path.join(ROOT, "02b_网页AI规范_轻量版.md"), "w", encoding="utf-8", newline="\n").write(lite)

    main = read(SRC_MAIN)
    main = (main.replace("<<EXPRESSION_LIB>>", expr)
                .replace("<<INTENT_MAP>>", intent)
                .replace("<<TECH_INDEX>>", tech_index)
                .replace("<<TECH_CARDS>>", tech_cards)
                .replace("<<EXAMPLE>>", ex))
    io.open(os.path.join(ROOT, "02_网页AI规范_完整自包含版.md"), "w", encoding="utf-8", newline="\n").write(main)

    # 03 全量技巧库（424 条精简字段）
    all_items = sorted(tech, key=lambda x: (CAT_ORDER.index(x["category_slug"]) if x["category_slug"] in CAT_ORDER else 99))
    out = ["# 电影技巧库 · 424 条全量精简版", "",
           "> 用法：先查主文件（02）第 5.1 节意图映射表拿到词条名，再来本文件按名字定位，抄它的 Prompt 模板。",
           "> 本文件为可选补充：主文件已内置 167 条高频卡，只有需要冷门词条时才追加本文件。", ""]
    for i, x in enumerate(all_items, 1):
        out.append(card(x, i))
        out.append("")
    io.open(os.path.join(ROOT, "03_技巧库_全量424条.md"), "w", encoding="utf-8", newline="\n").write("\n".join(out))

    sizes = {}
    for f in ["02b_网页AI规范_轻量版.md", "02_网页AI规范_完整自包含版.md", "03_技巧库_全量424条.md"]:
        print(f, os.path.getsize(os.path.join(ROOT, f)), "字节")
    for f in ["02_网页AI规范_完整自包含版.md", "03_技巧库_全量424条.md"]:
        sizes[f] = os.path.getsize(os.path.join(ROOT, f))
    print("02 主文件:", sizes["02_网页AI规范_完整自包含版.md"], "字节；词条卡", len(hot), "条")
    print("03 全量库:", sizes["03_技巧库_全量424条.md"], "字节；词条", len(all_items), "条")


if __name__ == "__main__":
    build()
