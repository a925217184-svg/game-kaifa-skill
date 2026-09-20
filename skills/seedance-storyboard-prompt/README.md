# seedance-storyboard-prompt

把**一句话想法 / 粗略剧本**变成 **Seedance 2.0 可直接跑的分镜提示词**。

不是 prompt 模板集合，而是一条带专业库的流水线：你的想法越粗，它补得越多——补镜头语言、补机位坐标、补电影灯光、补微表情、补同期声，最后输出**整段可复制**粘进生成器的 Shot 块。

---

## 它能干什么

| 能力 | 说明 |
| --- | --- |
| **想法优化（阶段零）** | 你说"这里要压迫感""反转要狠"，它从 424 条电影技巧库里挑 2–3 个候选，给推荐理由 + 改写前后对照，你拍板后才往下写 |
| **补全分镜（阶段一）** | 输出完整脚本：焦段 / 景别 / 景深焦点 / 机位数值 / 光照 / 站位 / 表情 / 台词 / 同期声 |
| **拼装提示词（阶段二）** | 回填参考图编号，输出整段可复制的 Shot 块，直接粘进 Seedance |
| **镜头语言选型** | 内置 melies.co 全站 **424 条**电影技巧（含 Prompt 模板），不凭感觉造镜头词 |
| **表情标准化** | 内置 **31 条**三行式表情词条（眼部+嘴角+面部），全片表情一致、可批量替换 |

三个阶段**不跳步**：阶段零给你提案 → 你拍板 → 阶段一给完整脚本 → 你确认 → 阶段二才拼提示词。不浪费生成额度。

---

## 内置资源

| 文件 | 内容 |
| --- | --- |
| `references/cinematic-techniques.md` | 424 条电影技巧全文（13 类），每条含定义、叙事功能、怎么拍、何时用/不用、片中实例、Prompt 模板、常见错误 |
| `references/cinematic-techniques.json` | 同上，结构化版，`search.py` 依赖它 |
| `references/intent-to-technique.md` | 意图映射表："压迫感 / 燃 / 反转 / 夜戏 / 国风…" → 具体词条，另附组合配方 |
| `references/expression-library.md` | 31 条表情标准词条（喜系 10 / 怒系 6 / 哀系 6 / 惊惧疑惑 4 / 高冷 5）+ 情绪递进链 |
| `references/seedance-prompt-spec.md` | 提示词规范真源：三层五块结构、镜头字段定义、全局红线、交付格式 |
| `scripts/search.py` | 技巧库检索工具（中文意图词 / 英文 / 分类过滤 / 精确取全文） |
| `scripts/crawl.py` `scripts/build_library.py` | 重抓与重建技巧库（源站更新时用） |

技巧库来源：<https://melies.co/cinematic-techniques>（CC 归属原站，本仓库仅作本地缓存便于检索）。

---

## 安装

### Windows PowerShell

```powershell
git clone https://github.com/a925217184-svg/game-kaifa-skill.git
cd .\game-kaifa-skill
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.workbuddy\skills" | Out-Null
Copy-Item -Recurse -Force ".\skills\seedance-storyboard-prompt" "$env:USERPROFILE\.workbuddy\skills\"
```

### macOS / Linux

```bash
git clone https://github.com/a925217184-svg/game-kaifa-skill.git
cd ./game-kaifa-skill
mkdir -p ~/.workbuddy/skills
cp -R ./skills/seedance-storyboard-prompt ~/.workbuddy/skills/
```

无需额外依赖（`search.py` 只用标准库；`crawl.py` 需要 `requests` 或 urllib 环境）。安装后重开会话让技能被干净载入。

---

## 怎么用

### 1. 调用

```
/seedance-storyboard-prompt
```

或者说人话触发：「写 Seedance 提示词」「补全分镜」「帮我优化这个想法」「这里镜头怎么拍」「这里用什么光」。

### 2. 丢想法（推荐模板，能填几项填几项）

```
/seedance-storyboard-prompt

想法/剧情：主角在帐里跟周瑜吹牛说要搞百万支箭，周瑜不信，结果真搞来了
想要的感觉：吹牛那段要拽，打脸那段要爽
风格：3D Q版次世代国风
时长/镜数：40s 8镜
画幅：9:16
参考图：（没生成就空着）
```

不填的项：风格套默认 3D Q 版次世代国风，时长默认 5s 一镜，画幅套 9:16 竖版，参考图位置写「待补」占位。

### 3. 你会拿到什么

**第 1 轮（阶段零）**：提案表——

| 意图 | 候选 | 推荐 | 理由 |
| --- | --- | --- | --- |
| 吹牛要拽 | Hero Cam / Low Angle / Slow Zoom In | Low Angle + Slow Zoom In | Hero Cam 要跟拍移动，帐内固定机位更适合慢推压迫感 |
| 打脸要爽 | Crash Zoom In / Smash Cut / Speed Ramp | Crash Zoom In | 一帧内怼脸，"认知崩塌"最干脆 |

外加改写前后对照。你回「就按这个」或「第二个换 Smash Cut」。

**第 2 轮（阶段一）**：完整分镜脚本，每镜含焦段 / 景深焦点 / 机位数值 / 光照 / 站位 / 表情【词条】 / 台词 / 同期声。

**第 3 轮（阶段二）**：整段可复制的 Shot 块——

```
Shot 01
风格：3D 卡通 Q 版次世代国风三国，PBR 材质，电影级游戏 CG，9:16 竖版。禁止：写实人脸、现代物品、多余角色、面部扭曲
镜头：虚拟 35mm 电影镜头，中近景，浅景深焦点锁定主角，低角度固定机位，极慢推近
拍摄内容：摄影机位于东吴水寨军帐内偏后方，距离地面 2.4 米高度，朝向营帐中央。夜晚帐内，暖黄油灯低位主光，帐门缝隙冷月逆光自左后方切入，硬光冷暖对撞。@玩家主角（束发金环，靛青金纹束发劲装）立于画面中下部、昂首抬手下压，双眼微眯、单侧轻挑，眼尾微扬，眼神灵动狡黠；单侧嘴角上扬偷笑、另一侧持平，嘴角不对称发力；单侧苹果肌轻微隆起，神态灵动俏皮、暗藏小骄傲，喝道："十万支箭？给将士剔牙都不够！我要翻十倍！"
同期声：帐外夜风声、拔剑金属摩擦声、人物对话声
时长：0-5 秒
```

---

## 单独查技巧库

```bash
python scripts/search.py 压迫感 --n 6          # 中文意图词
python scripts/search.py 出场 夜戏               # 多个意图词叠加
python scripts/search.py --en "slow zoom"        # 英文关键词
python scripts/search.py --en backlight --cat lighting
python scripts/search.py --name "Rembrandt Lighting" --full
python scripts/search.py --intent                # 列出全部内置中文意图词
```

内置 60+ 中文意图词：压迫感 / 紧张 / 爽感 / 燃 / 反转 / 悬念 / 震惊 / 孤独 / 宏大 / 亲密 / 悲伤 / 恐惧 / 慌张 / 得意 / 威严 / 打斗 / 追击 / 出场 / 落版 / 爆炸 / 时间流逝 / 闪回 / 梦境 / 夜戏 / 火光 / 冷暖对比 / 国风 / 科技感 / 赛博朋克 / 胶片感 ……

源站更新后重抓：

```bash
python scripts/crawl.py && python scripts/build_library.py
```

---

## 硬规则（这套流程踩过的坑）

1. **表情双写**：分镜脚本里写「表情【极致震惊】」简称便于你核对；**拼进提示词时必须展开成具体描述**（眼部+嘴角+面部），绝不出现词条名——模型不认词条名。
2. **一 Shot 一镜**：禁止镜内切镜，需要切镜就另开 Shot。
3. **机位必须数值化**：写"摄影机位于 X，离地 N 米"，不写模糊位置。
4. **景深必填**：浅景深要写明焦点锁在谁身上。
5. **交付整段可复制**：Shot 块内联风格与负面约束，参考图清单/备注挪到文件末尾，用户不拼接。
6. **参考图先占位**：图没生成时写「（参考图：待补）」，图到位只回填编号，不改其他内容。
7. **长图别走对话上传**：会被压成窄条不可读，给文件路径让 agent 本地切片读取。

---

## 目录结构

```
seedance-storyboard-prompt/
├── SKILL.md                      流程索引（agent 读这个）
├── README.md                     本文件
├── references/
│   ├── cinematic-techniques.md   424 条技巧全文
│   ├── cinematic-techniques.json 结构化版
│   ├── intent-to-technique.md    意图 → 技巧映射
│   ├── expression-library.md     31 条表情词条
│   └── seedance-prompt-spec.md   提示词规范真源
└── scripts/
    ├── search.py                 检索工具
    ├── crawl.py                  爬虫（重抓源站）
    └── build_library.py          建库
```
