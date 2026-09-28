# -*- coding: utf-8 -*-
"""把本地真源一次性同步到 GitHub 仓库副本。

用法：python _source/sync_to_repo.py

同步内容：
1. skills/seedance-storyboard-prompt/SKILL.md  （绝对路径 → 仓库相对路径）
2. skills/seedance-storyboard-prompt/references/seedance-prompt-spec.md（规范真源副本）
3. skills/seedance-storyboard-prompt/规则卡_v2.txt、references/expression-library.md
4. skills/seedance-storyboard-prompt/scripts/*.py（_tools 全量：search / count_chars / check_beats / effect_search）
5. web-ai-pack/ 整套刷新，并把其中的 build_pack.py 改成仓库相对路径版（clone 可原地重跑）
"""
import io, os, shutil

LOCAL_PACK = r"F:\AI视频制作\outputs\网页AI规范包"
LOCAL_SKILL = r"C:\Users\Administrator\.workbuddy\skills\seedance-storyboard-prompt"
LOCAL_SPEC = r"F:\AI视频制作\outputs\Seedance2.0_提示词规范_v1.0.md"
LOCAL_EXPR = r"F:\AI视频制作\outputs\人物表情描述库_v1.md"
LOCAL_CARD = r"F:\AI视频制作\outputs\规则卡_v2.txt"
REPO_ROOT = r"C:\Users\Administrator\WorkBuddy\game-kaifa-skill"
SKILL_DIR = os.path.join(REPO_ROOT, "skills", "seedance-storyboard-prompt")

BASE_PY = r"C:\Users\Administrator\.workbuddy\skills\seedance-storyboard-prompt\references\_tools\search.py"
BASE_MD = r"C:\Users\Administrator\.workbuddy\skills\seedance-storyboard-prompt\references"


def read(p):
    return io.open(p, encoding="utf-8").read()


def write(p, s):
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)


def sync_skill():
    """SKILL.md：绝对路径转仓库相对路径，并记录规则卡位置。"""
    t = read(os.path.join(LOCAL_SKILL, "SKILL.md"))
    t = t.replace(BASE_PY, "scripts/search.py")
    t = t.replace(BASE_MD, "references")
    t = t.replace("references/_tools/", "scripts/")
    t = t.replace(r"F:\AI视频制作\outputs\Seedance2.0_提示词规范_v1.0.md", "references/seedance-prompt-spec.md")
    t = t.replace(r"F:\AI视频制作\outputs\人物表情描述库_v1.md", "references/expression-library.md")
    t = t.replace(r"F:\AI视频制作\outputs\规则卡_v2.txt", "规则卡_v2.txt")
    t = t.replace(r"C:\Users\Administrator\.workbuddy\skills\seedance-storyboard-prompt\规则卡_v2.txt", "规则卡_v2.txt")
    t = t.replace(r"F:\AI视频制作\outputs\打斗提示词参考手册_v1.md", "references/combat-handbook.md")
    t = t.replace(r"F:\AI视频制作\outputs\网页AI规范包", "web-ai-pack")
    t = t.replace(r"C:\Users\Administrator\.workbuddy\skills\seedance-storyboard-prompt\references", "references")
    write(os.path.join(SKILL_DIR, "SKILL.md"), t)

    write(os.path.join(SKILL_DIR, "references", "seedance-prompt-spec.md"), read(LOCAL_SPEC))
    write(os.path.join(SKILL_DIR, "references", "expression-library.md"), read(LOCAL_EXPR))
    write(os.path.join(SKILL_DIR, "规则卡_v2.txt"), read(LOCAL_CARD))
    print("SKILL.md + spec + expr + card -> skills/seedance-storyboard-prompt/")


def sync_tools():
    """references/_tools/*.py → 仓库 scripts/（文件名不变，SKILL 里已按 scripts/ 引用）。"""
    src = os.path.join(LOCAL_SKILL, "references", "_tools")
    dst = os.path.join(SKILL_DIR, "scripts")
    if not os.path.isdir(dst):
        os.makedirs(dst)
    n = 0
    for f in sorted(os.listdir(src)):
        if f.endswith(".py"):
            shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
            n += 1
    print("scripts/ 刷新：%d 个工具" % n)


def sync_pack():
    """web-ai-pack 整套刷新 + build_pack.py 改相对路径。"""
    dst = os.path.join(REPO_ROOT, "web-ai-pack")
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(LOCAL_PACK, dst, ignore=shutil.ignore_patterns("__pycache__"))

    p = os.path.join(dst, "_source", "build_pack.py")
    t = read(p)
    pairs = [
        ("ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))",
         "ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # web-ai-pack/\n"
         "REPO = os.path.dirname(ROOT)                                          # 仓库根"),
        (r'SKILL = r"C:\Users\Administrator\.workbuddy\skills\seedance-storyboard-prompt"',
         'SKILL = os.path.join(REPO, "skills", "seedance-storyboard-prompt")'),
        (r'SPEC_DIR = r"F:\AI视频制作\outputs"',
         'SPEC_DIR = os.path.join(REPO, "web-ai-pack", "_source", "local_only")   # 仓库版不读本机绝对路径'),
        ('EXPR_LIB = os.path.join(SPEC_DIR, "人物表情描述库_v1.md")',
         'EXPR_LIB = os.path.join(SKILL, "references", "expression-library.md")'),
        ('COMBAT = os.path.join(SPEC_DIR, "打斗提示词参考手册_v1.md")',
         'COMBAT = os.path.join(SKILL, "references", "combat-handbook.md")'),
    ]
    for a, b in pairs:
        if a not in t:
            print("  [warn] 未匹配:", a[:56])
        t = t.replace(a, b)
    write(p, t)
    print("web-ai-pack refreshed:", sorted(os.listdir(dst)))


if __name__ == "__main__":
    sync_skill()
    sync_tools()
    sync_pack()
    print("同步完成，接下来：cd %s && git add -A && git commit && git push" % REPO_ROOT)
