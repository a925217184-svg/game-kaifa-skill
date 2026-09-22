# 镜头/特效写法查询库（Effect & Transition Writing Library）

> 真源：随技能分发。本库收录**跨镜头的高级特效序列 / 转场写法**，供写分镜 / 提示词时检索复用。
> 与 424 条电影技巧库（cinematic-techniques.md）互补：那库是**单镜头**语言，本库是**多镜头的特效序列/转场编排**。
> 查询：`python references/_tools/effect_search.py 变身 --full` / `尺度潜降 --full`，或 Grep 本文件（文件小，可整篇 Read）。
> 当前收录：① 变身 / 觉醒 / 形态切换 效果写法（提炼自两段参考提示词）② 尺度潜降微世界转场 写法。
> 调用约定：剧情含「变身 / 觉醒 / 形态切换 / 力量爆发 / 神格化 / 魔化 / 机甲合体 / 尺度潜降微世界转场」时，先查本库复用写法骨架，再写对应 Shot。

## 一、变身 / 觉醒 / 形态切换 效果写法

### 条目：龙 + 手镜圣光变身（参考提示词 1 · 原文）

参考原文（用户给的英文提示词，逐字保留以便复刻）：
A cinematic, high-action fantasy video sequence. An enormous, menacing dragon made of cracked volcanic rock and glowing orange magma attacks a floating, ancient Greek ruin high above the clouds. A young woman with long brown hair, wearing a simple white dress, is thrown to the ground as stone pillars collapse around her. She has blood on her lip but a defiant expression. She raises a golden, ornate hand mirror toward the sky, and a bright, blinding beam of golden sunlight shoots down from the heavens, engulfing her. The camera cuts to a macro close-up portrait of her transformation: her eyes glow with an intense, striking golden-orange color and reptilian-like irises, showing a small beauty mark on her left cheek and perfect skin texture under an intricate, sharp golden tiara with a prominent turquoise gemstone. The scene cuts back to a wide shot as she hovers high in the air above the ruins, now wearing a premium green and gold royal warrior uniform, ready to fight the lava dragon coiling around the floating platform. Dark smoky atmospheric background, epic scale, dramatic studio lighting, cinematic color grading, hyper-realistic production details, high-end CGI, 8K ultra-realism.

### 条目：冰原 + 火水晶火山变身（参考提示词 2 · 原文）

参考原文（用户给的英文提示词，逐字保留以便复刻）：
A continuous cinematic fantasy action sequence of a young East Asian warrior woman. She is crawling on a cracked icy battlefield, desperately holding up a glowing teardrop-shaped red crystal amulet set in a gold crescent. Suddenly, a massive surge of fiery energy explodes from the crystal, instantly shattering the ice and turning the entire landscape into a volcanic crater filled with flowing magma and ruined stone pillars. The woman levitates high into the air as intense, swirling vortices of fire wrap around her body. In mid-air, the flames materialize into a highly detailed crimson and gold fantasy dress with metallic arm guards and a flowing cape. A blazing crown of pure fire forms on her forehead, and her eyes snap open, glowing with intense, fiery heart-shaped patterns. She raises her hand to summon an intricate, giant golden magical circle in front of her, unleashing a catastrophic, blinding explosion of fire that obliterates everything in sight. 8K ultra-realism, high-fidelity VFX, dynamic camera angles, cinematic lighting, and epic scale.

### 通用骨架：变身四幕结构（复用模板 · 照填变量）

两段参考提示词共同遵循同一「变身四幕」序列，写任何变身桥段都套这个骨架，只换变量：

- **第一幕 · 受压 / 触发前（Weak State）**：主角处于弱势 / 危险（被击倒、爬行、受伤），特写脆弱细节（血迹、脏污、颤抖、破损衣物），建立「必须蜕变」的张力。写法：`thrown to the ground` / `crawling desperately` / `blood on lip but defiant expression`。
- **第二幕 · 触发器 + 能量贯入（Trigger & Infusion）**：精致发光的**英雄道具**向天 / 向敌举起 → 能量自天降或自道具爆发 → 包裹主角。这是变身「开关」。写法：`raises [hero object] toward the sky`；`a blinding beam of [color] shoots down from the heavens, engulfing her`；或 `a massive surge of [element] explodes from the [object], instantly [rewrites environment]`。
- **第三幕 · 形态切换微观高潮（Micro Beat）**：切 **macro close-up portrait**，展示新形态的「身份锚点」——发光异瞳、新头饰 / 冠、肤质、面部标记。这是让观众确认「她变了」的定帧。写法：`macro close-up portrait of her transformation`；`eyes glow with [color], [shape] irises`；`perfect skin texture under [headwear]`；`a small beauty mark on her left cheek`。
- **第四幕 · 亮相 / 力量展示（Reveal）**：回大全景 / 中景，主角已升空 / 换装完毕，新战甲新姿态，准备反击；常接一个终结技收尾。写法：`hovers high in the air above the ruins, now wearing [uniform], ready to fight`；`raises her hand to summon an intricate giant [magic circle], unleashing a catastrophic blinding explosion`。

### 通用写法要点（复刻时必带）

- **英雄道具作触发器**：道具材质具体化（`ornate golden hand mirror` / `teardrop-shaped red crystal amulet set in a gold crescent`）+ 发光 + 角色 `raises toward sky` 动作。它是变身开关，不是装饰。
- **能量包裹 + 材质具象化**：变身不是「啪一下换装」，而是能量体缠绕中「火焰 / 光逐部件凝实」（arm guards / cape / crown / tiara）。写法：`intense swirling vortices of [element] wrap around her body` → `[element] materializes into a highly detailed [outfit] with [parts]`。比直接写「她穿上了 X」更高级、AI 更稳定。
- **微特写身份锚点（必给 2–4 个）**：发光眼瞳形状（`reptilian` / `heart-shaped`）、肤色质感（`perfect skin texture`）、面部标记（`beauty mark on left cheek`）、头饰宝石（`prominent turquoise gemstone`）。让 AI 稳定生成「同一个新角色」，不蹦成陌生人。
- **环境随变身改写**：把环境变化写成变身能量的副产物（`massive surge turns landscape into volcanic crater`），强化力量规模，顺带省一个独立空镜。
- **风格签名块（可复用，贴每镜或结尾）**：`8K ultra-realism, cinematic lighting, epic scale, high-fidelity VFX, hyper-realistic production details, high-end CGI`。注意：本 skill 两区制下，质量词放说明区或全局锁风格串，别塞进每镜「拍摄内容」正文当元信息。

### 可复用英文 Prompt 词汇表（中英对照，直接抄）

- 受压：thrown to the ground / crawling desperately / blood on lip but defiant expression
- 触发：raises [hero object] toward the sky；a blinding beam of [color] shoots down from the heavens, engulfing her
- 能量爆发：a massive surge of [element] explodes from the [object], instantly [rewrites environment]
- 包裹：intense swirling vortices of [element] wrap around her body
- 具象：[element] materializes into a highly detailed [outfit] with [parts: arm guards / cape / crown / tiara]
- 微特写：macro close-up portrait；eyes glow with [color], [shape] irises；perfect skin texture under [headwear]；a small beauty mark on [left/right] cheek
- 亮相：hovers high in the air；now wearing [uniform]；ready to fight [enemy]
- 终结技：raises her hand to summon an intricate giant [magic circle], unleashing a catastrophic blinding explosion of [element]

### 变身避坑

- 变身不要「直接换装」：必须能量包裹 + 逐部件凝实，否则 AI 生成跳变 / 失真 / 换张脸。
- 微特写身份锚点不能省：没给发光眼 / 头饰 / 标记，AI 可能生成「换了个陌生人」。
- 终结技爆炸别写成常驻布景（参照全局锁「一次性特效写熄灭动作」硬规则）。
- 风格词堆在结尾 / 全局锁即可，别塞进每镜正文（违反两区制 / 正文禁元信息）。

## 二、尺度潜降微世界转场 写法

### 条目：尺度潜降微世界转场（骨架 + 命门 + 落地）

> 完整版见 `F:\AI视频制作\outputs\镜头技法_尺度潜降微世界转场_参考.md`。本条目为可调用精简版。

**定义**：从史诗大场景出发，锁定单一英雄物体 / 动作，镜头「贴着它飞 → 推到表面 → 无缝潜入纹理」，最终纹理本身变成一片微缩文明战场。核心卖点 = 尺度连续跳变 + match-cut 无缝转场。

**5 段轨迹骨架（铁律结构，照填变量）**：
1. 建立（Establishing）：史诗大广角，浩瀚场景 + 氛围（烟 / 尘 / 光），交待尺度。
2. 触发（Trigger）：一个孤独角色做「决定性动作」，释放英雄物体。
3. 飞行（Flight POV）：镜头瞬移到飞行物后方，极慢动作追捧，穿越烟灰 / 飞屑。
4. 推近（Push-in to surface）：持续 push-in，浅景深，物体占满画面，露出表面细节（纹路 / 木纹 / 雕饰 / 材质）。
5. 潜入（Dive into micro-world）：无缝尺度跳变——物体表面「变成地形」，微缩文明在上面开战。

**转场命门（写提示词逐条落实）**：
- match-cut 尺度连续：每段衔接用同一视觉元素承接（参考例 = 箭杆），大场景有它 → 飞有它 → 推近是它 → 微世界是它表面，元素不断裂。
- 纹理即世界（Texture-as-World）：微世界地貌必须视觉继承自主角物表面——雕文 = 峡谷绝壁、箭羽 = 战场地形、木纹 = 平原。不可自创美术。
- 浅景深 + 极慢动作反差：英雄物体永远锐利（浅景深 / 大光圈），背景混乱永远虚化；这是镜头签名，也卖速度 / 慢动作反差。

**AI 视频落地（真实能做，不是空想）**：
- 这一段**无法单次生成成一条连续镜头**，必须分段生成（Clip A~D）+ 拼接。
- Clip A = 建立 + 触发；Clip B = 飞行 POV（提示词强写 extreme slow motion, time dilation, drifting smoke, falling embers，后期可再降 fps）；Clip C = 推近至表面占满屏（浅景深强写）；Clip D = 微世界。
- **④→⑤ 用首尾帧锁定**：Clip C 末帧（物体表面占满屏）= Clip D 首帧（同一表面成为地貌），尺度跳变才无缝。
- **桥接参考图**：先单独生一张「英雄物体表面大特写」（带雕文 / 木纹 / 材质），既作 Clip C 锚点，又作 Clip D 首帧种子图（image2video / 首尾帧）。
- 微世界一致性：Clip D 提示词必须把「地貌 = 主角物表面」写死，否则会自创美术、跳戏。

**可替换变量表**：
- 必保留（按此参考不动）：5 段结构 / match-cut 尺度连续 / 纹理即世界 / 浅景深 + 极慢动作。
- 可换：大场景主题（古战场 / 星际 / 深海 / 都市）/ 英雄物体（箭 / 子弹 / 流星 / 信鸽 / 赛车）/ 表面纹理（雕文 / 电路 / 鳞甲 / 锈迹）/ 微世界设定（战士 / 机械虫 / 星舰 / 菌群）。

**可复用英文 Prompt 词汇（参考例，照改）**：
epic wide-angle, vast [scene], golden hour, thousands clashing, hazy amber sky thick with smoke and ash；camera snaps behind [object], extreme slow motion, cuts through drifting smoke and falling embers；shallow depth of field keeps [object] razor-sharp while [chaos] blurs behind；push closer until [surface] fills the frame — revealing [carved runes / weathered grain]；seamless transition to macro scale: [surface] becomes a landscape, microscopic civilization of tiny warriors wages war across the [fletching], miniature catapults hurl fragments of dust, [runes] like canyon walls, torches flicker, banners wave。
