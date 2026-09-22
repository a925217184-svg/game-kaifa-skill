# -*- coding: utf-8 -*-
"""
把本地真源（规范 / 表情库 / 424 条技巧库 / 意图映射表 / 打斗手册 / 实战示例）
组装成一份「自包含、可发给豆包 Gemini 等网页 AI」的规范包。

用法：python build_pack.py
输出：包根目录下 00_怎么用.md / 01_开场指令.txt / 02_网页AI规范_完整自包含版.md /
     02b_网页AI规范_轻量版.md / 03_技巧库_全量424条.md / 05_打斗手册.txt
"""
import io, os, json, re, textwrap

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = r"C:\Users\Administrator\.workbuddy\skills\seedance-storyboard-prompt"
SPEC_DIR = r"F:\AI视频制作\outputs"

SRC_MAIN = os.path.join(ROOT, "_source", "主体模板.md")
EXPR_LIB = os.path.join(SPEC_DIR, "人物表情描述库_v1.md")
INTENT_MAP = os.path.join(SKILL, "references", "intent-to-technique.md")
TECH_JSON = os.path.join(SKILL, "references", "cinematic-techniques.json")
EXAMPLE = os.path.join(SPEC_DIR, "奇迹MU风云助阵_Seedance提示词_v2_9秒5镜_可复制.txt")
COMBAT = os.path.join(SKILL, "references", "combat-handbook.md")

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


COMBAT_HEAD = """# 05 · 打斗提示词参考手册（网页 AI 自包含版）

> 本文件是《Seedance 分镜提示词规范》的**打斗场景专用补充**，与主文件 `02_网页AI规范_完整自包含版.md` 配套使用。

## 一、什么时候要用它

满足任意一条，就必须读本文件再动笔：

- 剧情里有 打斗 / 战斗 / 交手 / 对决 / 搏杀 / 追杀 / 群战 / 怪物搏杀 / BOSS 战；
- 用户提了「炫酷打斗 / 强化打击感 / 丰富特效 / 动作不流畅 / 打击没力度 / 节奏拖沓」这类需求词；
- 提示词里出现 兵器碰撞、能量对轰、变身觉醒后的战斗段落。

## 二、它和主规范怎么配合

| 层面 | 归谁管 |
|---|---|
| 全局锁、Shot 字段、两区制、字数上限、表情双写 | **主规范（02）**，一律照它 |
| 打斗内部的字段顺序、打击反馈、环境破坏、力量分级 | **本手册**，逐镜落 |
| 单镜的镜头语言 / 灯光词条选型 | 主规范第 5 节的 424 条技巧库 |

冲突时：**打斗场景内以本手册为准，其余一律以主规范为准。**

## 三、执行要求（写给 AI）

1. 逐镜固定字段序：`开局站位状态 → 镜头 → 动作 → 台词 → 情绪 → 特效 → 声音（前景/背景）`，不得跳序；
2. 每一处打击必须凑齐「接触闪 / 形变 / 位移 follow-through / 反作用力 / 二次破坏」五件，并配一个触点标记词（黑白闪 / 顿帧 / 音爆 / 震屏）；
3. 环境破坏走四段式：**场景层先预声明可破坏性 → 交手产生破坏 → 跨镜留残留痕迹 → 环境持续运动不停帧**；
4. 用户提需求词时，按 §5.1 映射表**取模块改字段**，不要重写全篇；
5. 本手册的所有产出同样受主规范的字数硬限制约束（「全局锁 + 目标 Shot」≤1800 字，硬上限 2000）。

---

"""


def build_combat():
    """把打斗手册真源转成网页 AI 自包含版（剔本地技能引用，加使用说明头）"""
    t = read(COMBAT)
    t = t.replace(
        "> 调用关系：本手册已挂入 `seedance-storyboard-prompt` 技能（`references/combat-handbook.md`）；剧情含",
        "> 调用关系：本手册是打斗场景的专用补充规范，与主规范配套使用。剧情含")
    t = t.replace("### §0.5 检索锚点（供 AI / 人工快速定位，可 Grep）",
                  "### §0.5 检索锚点（按此表直接翻到对应节）")
    t = re.sub(r"\n{3,}", "\n\n", t)
    # 正文 H1 降为 H2，避免与文件头 H1 并列；其余原样保留
    t = t.replace("# 打斗提示词参考手册 v1", "## 手册正文 · 打斗提示词参考手册 v1", 1)
    out = COMBAT_HEAD + "> 以下为手册正文，编号是两套：上方「一 / 二 / 三」讲怎么用，正文「§0–§5」是规范本体，执行时按 § 号定位。\n\n---\n\n" + t.strip() + "\n"
    io.open(os.path.join(ROOT, "05_打斗手册.txt"), "w", encoding="utf-8", newline="\n").write(out)
    print("05_打斗手册.txt", os.path.getsize(os.path.join(ROOT, "05_打斗手册.txt")), "字节")


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

    build_combat()

    sizes = {}
    for f in ["02b_网页AI规范_轻量版.md", "02_网页AI规范_完整自包含版.md", "03_技巧库_全量424条.md"]:
        print(f, os.path.getsize(os.path.join(ROOT, f)), "字节")
    for f in ["02_网页AI规范_完整自包含版.md", "03_技巧库_全量424条.md"]:
        sizes[f] = os.path.getsize(os.path.join(ROOT, f))
    print("02 主文件:", sizes["02_网页AI规范_完整自包含版.md"], "字节；词条卡", len(hot), "条")
    print("03 全量库:", sizes["03_技巧库_全量424条.md"], "字节；词条", len(all_items), "条")


if __name__ == "__main__":
    build()
