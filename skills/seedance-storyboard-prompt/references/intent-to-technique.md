# 意图 → 技巧 映射速查表

> 用途：用户给的想法往往是**感觉词**（"压迫感""燃一点""反转要狠"），本表把感觉词翻译成库内**具体词条**。
> 检索命令：`python <skill>/references/_tools/search.py 压迫感 --n 6`（支持多个意图词叠加、加 `--full` 看全字段、加 `--cat lighting` 限定分类）。
> 列出全部内置意图词：`python search.py --intent`。
> 表内词条名**均真实存在于** `cinematic-techniques.md`，可直接 Grep 取全文。

## 使用原则

1. **先翻译，再选型**：用户说"要压迫感" → 本表给出候选 → 按项目风格/画幅筛掉不合适的 → 挑 1–2 条落到 Shot 的「镜头」「光影」字段。
2. **镜头运动 ≠ 情绪万能药**：一条 Shot 只用**一种主导运动**，别把 Slow Zoom In + Handheld + Whip Pan 堆一起（模型会糊）。情绪靠「运动 + 角度 + 光 + 景别」组合表达。
3. **注意反例**：少数词条的 Prompt 模板段落可能是"不要这样拍"的反例（如 Low Angle 的模板含 "no dramatic upward angle"），引用前扫一眼 `何时用/常见错误` 字段。
4. 本表是**起点不是终点**：命中后仍要读该词条的「何时不用」确认适用。

---

## 一、情绪 / 氛围

| 用户说 | 首选词条 | 备选 | 搭配建议 |
|---|---|---|---|
| 压迫感 / 被盯上 / 喘不过气 | Slow Zoom In、Push In | Low Angle、Worm's-Eye View、Chiaroscuro、Telephoto Compression | 慢推 + 低角度 + 低调光，5s 内只做一件事 |
| 紧张 / 悬着心 | Dutch Angle、Handheld | Rack Focus、Low-Key Lighting、Quick Cuts | 轻微倾斜（5–10°）即可，别过 |
| 爽感 / 打脸 / 解气 | Crash Zoom In、Speed Ramp | Whip Pan、Slow Motion、Hero Cam、Bokeh | 前镜压 → 本镜爆，节奏从慢到快 |
| 燃 / 热血 / 高燃 | Low Angle、Crane Up | Orbit、Slow Motion、Sparks and Embers、Halation、Motion Blur | 仰角 + 上升 + 火星粒子 |
| 反转 / 打脸时刻 | Dolly Zoom、Crash Zoom In | Smash Cut、Focus Change、Reverse Angle、Epiphany | Dolly Zoom 是"认知崩塌"的教科书做法 |
| 悬念 / 藏着不说 | Slow Zoom In、Voyeur | Dirty Frame、Silhouette、Rack Focus、Low-Key Lighting | 用遮挡（Dirty Frame）比用黑屏高级 |
| 震惊 / 不敢相信 | Crash Zoom In、Smash Cut | Freeze Frame、Dolly Zoom、Flash Cut、Extreme Close-Up (ECU) | 极速推近 + 定格，配表情库【极致震惊】 |
| 孤独 / 一个人 | Negative Space、Extreme Long Shot (ELS) | High Angle、Cool Blue、Desaturation、Wide Shot (WS) | 人小景大 + 冷调 |
| 宏大 / 气派 / 大场面 | Extreme Long Shot (ELS)、Crane Up | Aerial、Establishing Shot、One-Point Perspective、Symmetry | 竖版（9:16）改用**纵向延伸 + 上升运动** |
| 亲密 / 温情 / 暖 | Close-Up (CU)、Shallow Focus | 85mm Portrait、Soft Light、Two-Shot、Warm Amber、Bokeh | 浅景深必须写明焦点锁谁 |
| 悲伤 / 失落 | Cool Blue、Desaturation | Rain、Slow Motion、High Angle、Cameo Lighting | 配表情库【心酸难过】/【隐忍含泪】 |
| 恐惧 / 阴森 | Underlighting、Chiaroscuro | Dutch Angle、Low-Key Lighting、Handheld、Night Vision、Cosmic Horror、Film Noir | 底光（Underlighting）最出恐怖感 |
| 慌张 / 乱了阵脚 | Handheld、Whip Pan | Dutch Angle、Quick Cuts、Stutter / Stop-Stutter、Jump Cut | 配角专用，主角保持稳 |
| 得意 / 装到了 | Low Angle、Hero Cam | Slow Motion、Bokeh、Three-Quarter Angle | 配表情库【得意窃喜】/【明媚爽朗】 |
| 威严 / 王霸之气 | Low Angle、Worm's-Eye View | Symmetry、Centered Composition、Rembrandt Lighting、Top Light | 居中 + 对称 + 仰拍 = 权威三件套 |
| 神秘 / 看不清 | Silhouette、Backlight | Fog、Cameo Lighting、Voyeur、Volumetric Light | 逆光剪影 + 体积光 |

## 二、场面 / 动作

| 用户说 | 首选词条 | 备选 | 搭配建议 |
|---|---|---|---|
| 打斗 / 对战 | Handheld、Speed Ramp | Slow Motion、Match on Action、Bullet Time、Sparks and Embers、Close-Up (CU) | 变速（Speed Ramp）比全程慢动作更有冲击力 |
| 追击 / 逃跑 | Tracking Shot、Steadicam | FPV Drone、Whip Pan、Speed Ramp、Parallax、Car Chasing | 加 Foreground Interest 出速度感 |
| 出场 / 登场 / 亮相 | Low Angle、Crane Up | Dolly In、Silhouette、Rim Light、Hero Cam、Backlight | 先剪影后亮脸两步走（拆两 Shot） |
| 高潮 / 最炸的一下 | Crane Up、Orbit | Slow Motion、Speed Ramp、Montage、Low Angle、Sparks and Embers | 单个 Shot 装不下就拆 |
| 落版 / 定格收尾 | Freeze Frame、Crane Up | Aerial Pullback、Symmetry、Static Locked-Off、Vignette | 竖版落版：主体占上 2/3，底部留 1/3 给 CTA |
| 爆炸 / 火攻 / 大火 | Sparks and Embers、Smoke | Light Flash、Slow Motion、Particles、Fire、Chiaroscuro | 火光用 Motivated Lighting 说明光源动机 |
| 战争 / 千军万马 | Long Take、Handheld | Desaturation、Dust and Sand、Smoke、Wide Shot (WS)、Oner | 大场面配 Wide + 烟尘 |
| 速度感 | Motion Blur、Speed Ramp | Low Shutter、Whip Pan、Tracking Shot、Timelapse Human | — |
| 混乱 / 打成一锅粥 | Handheld、Dutch Angle | Quick Cuts、Dirty Frame、Asymmetry、Stutter / Stop-Stutter | — |

## 三、时间 / 叙事

| 用户说 | 首选词条 | 备选 | 搭配建议 |
|---|---|---|---|
| 时间流逝 / 过了很久 | Time-Lapse、Hyperlapse | Dissolve、Montage、Timelapse Landscape | — |
| 回忆 / 想起 | Dissolve、Filmic Faded | Soft Light、Vintage、Sepia、Bokeh | 配合降低饱和 |
| 闪回 | Flash Cut、Smash Cut | Dissolve、Desaturation、Sepia、Jump Cut | — |
| 梦境 / 不真实 | Dreamcore、Double Exposure | Morph、Soft Light、Halation、Weirdcore、Slow Motion | — |
| 幻觉 / 中毒 / 系统侵入 | Altered State、Datamosh | Chromatic Aberration、Kaleidoscope、LSD、Thermal、Double Exposure | 系统流弹窗可配 Floating UI |
| 一镜到底 | Long Take、Oner | Steadicam、Invisible Cut、Match on Action | AI 生成 5s 内更稳 |
| 转场 | Match Cut、Whip Pan | Invisible Cut、Graphic Match、Dissolve、Wipe、Smash Cut | 注意：本技能要求一 Shot 一镜，转场通常发生在 Shot 之间 |

## 四、光线 / 色彩

| 用户说 | 首选词条 | 备选 | 搭配建议 |
|---|---|---|---|
| 夜戏 | Low-Key Lighting、Moonlight Gel | Blue Hour、Practical Lighting、Silhouette、Day for Night、Neon Practicals | — |
| 白天外景 | High-Key Lighting、Naturalistic Ambient | Bounce Light、Golden Hour、Available Light | — |
| 黄金时刻 / 夕阳 | Golden Hour、Backlight | Lens Flare、Halation、Warm Amber、Long Shot (WS) | — |
| 火光 / 火把 / 油灯 | Practical Lighting、Sparks and Embers | Underlighting、Warm Amber、Motivated Lighting、Chiaroscuro | 必须写明光源动机（谁在发光） |
| 冷暖对比 | Teal and Orange、Split Toning | Cross Lighting、Tonal Contrast、Motivated Lighting | 军帐=暖油灯 vs 冷月光就是典型 |
| 烛光 / 帐内暖光 | Candlelight、Practical Lighting | Chiaroscuro、Warm Amber、Eye Light | Eye Light（眼神光）保证眼睛不死 |
| 室内自然光 | Window Light、Practical Lighting | Three-Point Lighting、Bounce Light、Naturalistic Ambient | — |
| 雾 / 雨 / 雪 / 沙尘 | Fog、Mist、Rain、Snow | Atmospheric Haze、Dust Motes、Dust and Sand、Steam、Smoke | 雾配体积光出丁达尔 |

## 五、风格

| 用户说 | 首选词条 | 备选 | 搭配建议 |
|---|---|---|---|
| 国风 / 东方 / 古风 | Wuxia、Ink Riot | Hand Paint、Paper、Origami、Symmetry、Golden Ratio | 三国国风主打 Wuxia + Symmetry |
| 武侠 / 打戏飘逸 | Wuxia、Slow Motion | Crane Up、Sparks and Embers、Mist | — |
| 科技感 / 系统 UI | Floating UI、Tech Noir | Neon Practicals、Volumetric Light、Random Glow、Blue Depth | 系统弹窗画面内生成时用 Floating UI |
| 赛博朋克 | Neon Practicals、Tech Noir | Dystopian、Cool Blue、Volumetric Light、Ultraviolet、Night Vision | — |
| 复古 / 怀旧 | Vintage、Filmic Faded | Sepia、Film Grain、Halation、Vintage Cine Glass、2000s Paparazzi | — |
| 胶片感 | Film Grain、Halation | Bleach Bypass、Cross Process、Anamorphic、Filmic Faded | — |
| 高级感 / 精致 | Soft Light、Glam | Bokeh、Shallow Focus、Teal and Orange、Anamorphic、Symmetry | — |
| 电影感 | Anamorphic、Shallow Focus | Lens Flare、Teal and Orange、Film Grain、Halation | — |
| 游戏 CG 感 | Video Game、3D Render | Blockbuster Gloss、Diorama、Photogrammetry | 本片默认基底 |
| 动画 / 卡通 / Q 版 | Animation、Comic | Flash Comic、Hand Paint、Paper、Pixel Art | Q 版次世代国风的基础层 |

---

## 附：常见组合配方（可直接套）

| 场景 | 配方 |
|---|---|
| 主角放狠话（爽点） | Low Angle + Slow Zoom In + Rim Light + 暖 Practical + 表情【得意窃喜】 |
| 配角被打脸（反应镜） | Medium Close-Up (MCU) + Crash Zoom In + 冷调 + 表情【极致震惊】 |
| 大场面登场 | Extreme Long Shot (ELS) → Crane Up + Silhouette + Backlight + Sparks and Embers |
| 夜帐密谋 | Three-Point Lighting 降级为 Candlelight + Chiaroscuro + 冷月光窗光 + Slow Zoom In |
| 系统弹窗触发 | Close-Up (CU) + Shallow Focus（焦点锁弹窗）+ Floating UI + Eye Light |
| 落版定格 | Crane Up + Symmetry + Freeze Frame + Vignette（竖版：底部留白给 CTA） |
