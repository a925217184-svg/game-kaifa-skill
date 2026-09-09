# cocos2d-atlas-builder

把**有序的透明 PNG 序列帧**打包成方形精灵图集（N×N 网格），并生成
**标准 Cocos2d `.plist`**（严格对齐 Free Texture Packer 的 Cocos2d 导出模板），
可直接被 Cocos Creator / cocos2d-x 正确导入。

适合：动画角色 / 特效帧 → 单张透明图集 + 可用 plist（含 8×8 与 4×4 体积对比）。

---

## 功能

- **`build_atlas.py`** — 有序 PNG 帧 → 方形透明图集
  - 生成 `<name>.png`（透明底）、`<name>.atlas`（libGDX 风格帧描述）、`frames/`（单帧）、`preview_<name>.png`（带编号的网格预览）
  - 支持 N×N 网格（如 `--grid 4` → 16 帧 1024²，`--grid 8` → 64 帧 2048²）
  - 强制保留首/尾帧，中间帧按播放顺序均匀抽帧（循环不跳）
  - LANCZOS 缩放到统一格子尺寸，保持猫/角色相对位置
- **`gen_plist.py`** — `.atlas` → 标准 Cocos2d `.plist`
  - format=2、pixelFormat=RGBA8888、premultiplyAlpha
  - rect 字符串无空格（`{{0,0},{256,256}}`），2 空格缩进
  - 写盘后用 `plistlib` 自检
- **`make_preview_gif.py`** — `frames/` → 播放 GIF，肉眼核对循环
- **`build_with_texturepacker.py`** — **推荐路径**：先归一化每帧（裁内容框→统一缩放→居中/脚底对齐），再调用本机 TexturePacker CLI 出「干净边缘」图集 + cocos2d plist（format=3）。适合对切单帧脏边 / 串帧零容忍的场景。

> 注意：本工具只做**图集打包 + plist 生成**。上游的抠图 / 绿幕去背（产出透明帧）不在此范围内，喂干净透明帧进来即可。

---

## 安装

### 方式 A：作为 WorkBuddy 技能（推荐）
把整个目录放到用户级技能目录，即可被 WorkBuddy 自动触发：

```bash
# 目录结构需为：
~/.workbuddy/skills/cocos2d-atlas-builder/
├── SKILL.md
├── README.md
├── scripts/
│   ├── build_atlas.py
│   ├── gen_plist.py
│   └── make_preview_gif.py
└── references/
    └── cocos2d_plist_spec.md
```

### 方式 B：作为普通脚本使用
克隆后直接用 Python 运行（见下方用法）。

---

## 依赖

```bash
pip install pillow numpy
```

---

## 用法

### 1) 生成图集

```bash
python scripts/build_atlas.py \
  --src  /path/to/ordered_frames \
  --out  /path/to/output \
  --name cat_pink \
  --grid 4 \          # 4 -> 4×4 = 16 帧；8 -> 8×8 = 64 帧
  --cell 256 \        # 每帧缩放到 256×256
  --defringe-green    # 可选：去除残留绿幕边缘
```

产出 `output/cat_pink.png` + `cat_pink.atlas` + `frames/` + `preview_cat_pink.png`。

### 2) 生成 plist

```bash
python scripts/gen_plist.py \
  --atlas /path/to/output/cat_pink.atlas \
  --out   /path/to/output/cat_pink.plist
```

输出示例：`plist=cat_pink.plist frames=16 format=2 RGBA8888 -> OK`。

### 3) 预览 GIF（可选）

```bash
python scripts/make_preview_gif.py \
  --frames /path/to/output/frames \
  --out    /path/to/output/playback.gif \
  --fps 12 --resize 256
```

### 多版本对比（8×8 vs 4×4）
用不同 `--grid` 各跑一次（不同 `--out`），再各自生成 plist，比较体积后选更小的接入 Cocos。

### 4) TexturePacker 路径（干净边缘，推荐）

当本机装了授权版 TexturePacker 时优先用它。它能原生输出标准 cocos2d plist（format=3），
并且其 `--extrude` / `--shape-padding` / `--border-padding` 是处理"切单帧边缘脏线/串帧"的
业界标准做法。

```bash
python scripts/build_with_texturepacker.py \
  --src  /path/to/ordered_frames \
  --out  /path/to/out \
  --name passerby_1_happy \
  --grid 4 --sheet 1024 \
  --content-max 224 --cell-prep 240 \
  --tp "C:/Program Files/CodeAndWeb/TexturePacker/bin/TexturePacker.exe"
```

要点：
- 脚本会先把每帧裁到 alpha 包围盒 → 统一缩放（最长边 = `--content-max`）→ 居中(水平)/脚底对齐进
  `--cell-prep` 画布，保证 4×4 网格里角色大小一致、不漂移。
- 再调用 TexturePacker：`--algorithm Grid --shape-padding 4 --border-padding 4 --extrude 2
  --disable-rotation --trim-mode None --trim-sprite-names`，相邻帧之间有 ≥8px 透明 gutter，
  即使 Cocos 开 mipmap 也不会切到邻帧。
- 约束：`(cell-prep + shape-padding) × grid ≤ sheet`。4×4@1024 用 cell-prep=240（(240+4)×4=976）。
- 进 Cocos 后把纹理 **Filter Mode 设为 Bilinear**（非 Trilinear），或 `.png.meta` 里
  `genMipmaps:false`，双保险。

### 4b) 保持原图比例、不裁切像素（消除帧间跳动，推荐用于同源等尺寸序列帧）

当所有源帧已经是**同一尺寸**（例如渲染序列帧全是 960×960），且你希望角色在循环播放时
**完全不动（无缩放/无位移抖动）**，改用 `--keep-ratio --pad 4`，不要传 `--content-max`：

```bash
python scripts/build_with_texturepacker.py \
  --src  /path/to/ordered_frames \
  --out  /path/to/out \
  --name passerby_1_happy \
  --grid 4 --sheet 1024 --cell-prep 240 \
  --keep-ratio --pad 4 \
  --tp "C:/Program Files/CodeAndWeb/TexturePacker/bin/TexturePacker.exe"
```

它和「裁切归一化」路径的区别：
- **不做 alpha 包围盒裁剪** —— 原图每个像素都保留（只整体缩放），不会丢失透明边距、也不会
  重新取景主体；
- **全序列用同一个全局 scale** = `(cell-prep − 2·pad) / 最长边`，每张帧都套这个系数 →
  相对大小/位置完全锁定 → 循环播放零跳动；
- 每帧居中进 `cell-prep` 画布；因为同源序列取景一致，主体在整段循环里都钉在原地。

> 取舍：keep-ratio 下角色在 cell 内会偏小（保留了原图透明边距、未裁），这是「不裁切像素」
> 的必然结果。若想角色更大又不抖，可改用「全帧统一裁同一包围盒 + 同一 scale」的折中方案。

---

## plist 规范要点

| 字段 | 值 |
|------|----|
| DOCTYPE | `-//Apple Computer//DTD PLIST 1.0//EN` |
| metadata.format | `2` |
| metadata.pixelFormat | `RGBA8888` |
| metadata.premultiplyAlpha | `false` |
| rect 字符串 | 无空格：`{{x,y},{w,h}}` |

常见失败：rect 带空格（`{{0, 0},{256, 256}}`）会让 Cocos 正则解析抛
`reading 'slice'/'indexes'`。完整说明见
[references/cocos2d_plist_spec.md](references/cocos2d_plist_spec.md)。

---

## 许可证

MIT
