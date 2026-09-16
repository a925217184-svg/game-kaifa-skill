---
name: html-game-to-cocos
description: 把单文件 HTML/Canvas2D 游戏移植为 Cocos Creator 工程的一条完整流水线：矢量忠实移植 → funplay-cocos-mcp 编辑器自动化（节点实体化/槽位批量创建/场景修改/编译诊断）→ Sprite 槽位机制（拖图即替换、无图矢量兜底）→ 动态元素实体化 → 手册交付。用户提供 HTML 游戏要求转成 Cocos、要求"编辑器里能看见节点、替换 PNG 素材"、或需用 MCP 操作 Cocos 编辑器时使用。
---

# HTML 游戏 → Cocos 可视化可替换工程（单一流水线，MCP 驱动）

来源：猫猫村项目实战验证（Trae + WorkBuddy 协作全过程复盘，2026-09）。

**核心认知：HTML 变成 Cocos 工程，靠的就是 MCP。** 矢量移植只是把代码写对；真正让用户"在编辑器里看见节点、拖图替换素材"的每一步——节点实体化、槽位批量创建、场景修改、编译诊断、调试闭环——全部通过 funplay-cocos-mcp 在编辑器进程内自动完成。

## 流水线总览

```
HTML 单文件游戏
  ↓ Step 1  矢量忠实移植（纯代码，先跑起来：挂一个组件 = 完整画面）
  ↓ Step 2  MCP 节点实体化（运行时黑盒 → 编辑器真实节点）
  ↓ Step 3  MCP 批量建 Sprite 槽位（拖图即替换、无图矢量兜底）
  ↓ Step 4  动态元素实体化（网格/角色/序列帧动画）
  ↓ Step 5  迭代调试闭环（recompile → diagnostics → DEBUG 日志）
  ↓ Step 6  清理 + GUIDE.md 交付
= 用户拿到：打开工程即运行、全部元素可视化、素材即拖即换、参数全可调
```

---

## MCP 基础设施（流水线的传动装置，所有 Step 共用）

### 架构与接入

- **funplay-cocos-mcp**：Cocos 编辑器内置插件，HTTP MCP 服务（默认端口 8765/8766，以编辑器控制台显示为准），核心工具 `execute_javascript`——在 Cocos 编辑器进程内直接执行 JS。
- WorkBuddy 侧封装：工程 `scripts/mcp.mjs` 转发，三种用法：
  - `node scripts/mcp.mjs js editor <file.js>` —— **editor 上下文**：有 `Editor` 对象，走 `Editor.Message.request(...)`，**修改可持久化**
  - `node scripts/mcp.mjs js scene <file.js>` —— **scene 上下文**：有 `cc` 全局，直接操作场景节点（find/addComponent/设属性），配 `save-scene` 落盘
  - `node scripts/mcp.mjs call <tool> '<json>'` —— 插件其它工具（如 `run_script_diagnostics`）

### 双上下文决策表

| 任务 | 用法 | 持久化 |
|---|---|---|
| 读/改 1 个已知文件、跑 1 条命令 | 直接 Read/Edit/Shell，**不要绕道 MCP** | — |
| 改代码后重编译 + 类型诊断 | js editor：recompile + run_script_diagnostics | — |
| 批量创建/修改场景节点（图层、槽位、Widget、组件） | js scene：写 `scripts/stepN_*.js` 一次性脚本 → 顶层 `return JSON.stringify(out)` → `save-scene` | ✅ |
| 查节点树/组件状态 | js scene：walkAll 遍历 + 顶层 return | 只读 |
| 预览运行时里建节点 | ❌ 退出预览即消失，禁止用于持久化 | ❌ |
| 触发构建 wechatgame | ❌ 3.8.8 builder 无触发消息，只能用户在构建面板手动点 | — |

### 一次性脚本模式（每个 Step 的批量操作都长这样）

```javascript
// scripts/step3_create_slots.js —— 命名带 Step 前缀，可复跑
const out = { created: [], skipped: [] };
function walkAll(root, fn) { fn(root); root.children.forEach(c => walkAll(c, fn)); }
const rootNode = /* find('GameRoot') */;
// ... 查找 → getComponent → 创建/改属性 → updateAlignment() ...
return JSON.stringify(out);   // ★ 只捕获顶层 return；IIFE 内部 return 捕获不到
```

- 结果必须**顶层 return**，`out` 带 before/after 便于核对；脚本留存 `scripts/` 可复跑；跑完 editor 上下文执行 `save-scene` 落盘。

### MCP 已知坑（实战踩过，违者必翻车）

| 坑 | 对策 |
|---|---|
| `cc.Widget.AlignFlag` 枚举在脚本里 undefined | 直接用位值：TOP\|BOT\|LEFT\|RIGHT = 1\|4\|8\|32 = 45 |
| 变量名 `scene` 与上下文冲突（"already declared"） | 换名（如 `rootNode`）；MCP 已知噪音报错，不管它 |
| `node.on(TOUCH_END, ...)` 事件绑定 | **不序列化进 .scene**，重开即丢 → 事件必须在脚本 onLoad 里绑 |
| 动态 addComponent 的组件 | 不进 Inspector，@property 配置无效 → 需要面板配置的组件必须场景静态挂载 |
| `@property` 数组内联初始化 `= [new X()...]` | 反序列化时覆盖用户拖的配置 → 声明 `= []` 运行时补位 |
| `@ccclass('类名')` 改名 | .scene 序列化硬引用 → "Class xxx is missing" |
| Sprite sizeMode | 必须 CUSTOM，否则图片原始尺寸覆盖布局尺寸 |
| SpriteAtlas 帧序 | `spriteFrames` 字典 + `localeCompare(numeric:true)` 自然排序 |
| 每帧重绑渲染器 + once 动画 | bind() 必须保留进行中 forward-once/reverse-once 的 frameIndex，否则动画不前进 |
| 禁止未经用户确认删 assets 资源 | 曾误删 plist 引发导入器连锁崩溃 |

---

## Step 1 矢量忠实移植（先让它跑起来）

1. 通读 HTML：确认坐标系统（通常 top-left 设计分辨率如 720×1280）、主循环、状态机、输入、音效合成方式。
2. 固定文件结构：
   - `GameConfig.ts`：全部可调参数 `@property` 曝出 + 中文 tooltip（布局/节奏/权重/坐标/通关失败条件）。
   - `DrawUtil.ts`：**Canvas 语义包装器类 `C`**（fillRect/fillCircle/text → Graphics，内部统一换算 y 轴与角度）+ 全部矢量绘制函数。
   - `GameRoot.ts`：唯一入口组件。onLoad 自动构建图层子节点；状态机 + 主循环 + 输入全在里面。
   - `RendererBase.ts`（基类：UITransform + Graphics + C 实例 + 每帧 beginFrame/clear）+ 每层一个 Renderer（Background/Grid/Passerby/Flying/Drag/UI/Panel，z 序按 HTML 的 render() 绘制顺序）。
   - `AudioController.ts`（WebAudio 合成）。
3. ★ 坐标约定：**逻辑层保留 H5 的 top-left 设计坐标**，由 `C` 包装器内部换算成 Cocos 中心坐标——逻辑代码零改动、可与 HTML 逐函数对照。
4. ★ 逐函数移植：build/ensure/remove、spawn/update、tryPlace/hitTest、end/fail/reset 与 HTML 一一对应命名。

**Step 1 必踩坑**：
- 装饰器**只能** `import { _decorator } from 'cc'; const { ccclass, property } = _decorator;` —— ❌ 别名 `@cc()`、❌ 直接 `import { ccclass } from 'cc'`，都会编译成 `ccclass is not a function`。
- 报错后清 `temp/` + `library/` 让编辑器全量重编译（增量 chunk 缓存会继续用坏代码）。
- 引擎 `.d.ts` 的几十个诊断错误是噪音，只过滤 `assets/scripts`。
- `.meta` 只能由编辑器生成——**脚本堆不是 Cocos 工程**，必须放进编辑器初始化过的工程目录。
- 显式降级：`getFrames(i) || getFrames(0)` 这类 fallback 会把所有缺失配置伪装成同一表现（曾致 6 个路人全显示同一形象），宁可显式 warn + 走兜底渲染。

## Step 2 MCP 节点实体化（运行时黑盒 → 编辑器真实节点）

1. `mkLayer` 改为：**优先 `getChildByName` 复用场景已有节点，找不到才动态创建**（两条路径兼容）。
2. 写 `scripts/step2_create_layers.js`（js scene），批量创建 7 个图层节点：
   - 规格：layer=UI_2D、UITransform=设计分辨率、锚点 0.5、挂 Graphics + 对应 Renderer；
   - z 序按 HTML render() 绘制顺序（`move-array-element` 修正或按创建顺序）；
   - 结束 `save-scene` 落盘。
3. ★ **绝不手写 `.scene` JSON**（压缩 uuid / 组件 `__type__` 编码无法可靠手写，必然错位炸场景）。必须走编辑器场景 API（MCP）。

## Step 3 MCP 批量建 Sprite 槽位（拖图即替换、无图矢量兜底）

- `RendererBase.spriteSlot(name)`：本层子树找同名（支持前缀匹配，兼容中文备注后缀）+ 跨层回退查找；**有 spriteFrame → 用图，没有 → 代码矢量兜底**。`ph-` 占位色块编辑器可见、运行时自动隐藏。
- 写 `scripts/step3_create_slots.js`（js scene）批量建槽位节点：UITransform(语义默认尺寸) + Sprite(**sizeMode=CUSTOM**) + 纯色占位块，命名 = 元素语义名：
  `bg-wall / bg-window / bg-floor / bg-carpet / bg-table / hud-counter-bg / hud-progress-track / hud-progress-fill / panel-start-bg / button-start ...`
- 按钮 = Sprite 槽位 + Button 组件（换图保功能，事件在脚本 onLoad 绑）；文字 = Label 节点；面板逐元素拆槽位（底板/标题/按钮独立）。
- 交付 `GUIDE.md`：槽位清单（名称/层级/默认尺寸/替换步骤）+ 参数清单 + 验收清单。

## Step 4 动态元素实体化（同样经 MCP 脚本建节点）

- **网格类**：`grid-cat-0..N` 实体节点兼作**布局真源**——运行时读节点位置生成格子坐标；用户对齐自定义背景图只需拖这些节点；可另做自动对齐脚本。
- **角色类**：`body-sprite / nest / nest-cat-0..2 / drag-cat / fly-cat` 实体节点；嵌套节点缩放用世界缩放换算对齐（相对父层缩放 × 目标世界缩放）。
- **序列帧动画**：`CatAtlasGroup` —— 用户只拖 SpriteAtlas（plist+png 导入自动切帧），代码帧名自然排序播放，按 `品种_动作` 组合索引。禁止让用户逐帧手填。
- **★ 定位红线**：依赖移动节点的效果（特效/飘字/粒子落点）必须**每帧实时取节点位置**，禁止用触发时快照（快照必偏移）；"代码定位 + 编辑器动画驱动位移"冲突时用**锚点容器模式**——动画写相对坐标、静止锚点承担定位（锚点 = base − clip 首帧录制值）。
- 随机化需求（如出场乱序）用不重复抽取袋（charBag），避免相邻重复。

## Step 5 迭代调试闭环（MCP 驱动，贯穿 Step 2~4 的每一轮）

```
改代码/改场景 → node scripts/mcp.mjs js editor scripts/recompile.js
  → run_script_diagnostics 过滤 assets/scripts = 0 错误
  → 让用户"停止预览 → 重新运行"
  → 有问题：关键路径加 [DEBUG-阶段] log（一次 ≤4 处，覆盖 生产方→传递方→消费方 三环）
  → 用户贴日志/截图 → 日志字段值是真相，缺哪环断在哪环；截图先读 Inspector 真实值再怀疑代码
  → 涉及场景的修正 → step*_fix.js 脚本 + save-scene
```

## Step 6 清理 + 交付

- 清理移植期遗留的作废接口（旧 texture/rows/cols 手动切帧路径等）。
- 跑诊断确认 `assets/scripts` 0 错误；更新 GUIDE.md。
- 验收清单：编辑器打开可见全部槽位色块 / 删掉槽位回退矢量 / 拖图即替换 / 预览与 HTML 一致 / 参数全可调。

---

## 用户工作流约定

- 替换顺序：静态（背景/HUD）→ 面板 → 动态角色 → 序列帧动画，逐批交付，每批都要求"编辑器里看得见"。
- 位置调整优先给"自动对齐脚本"（MCP 生成），不让用户手算坐标。
- 所有坐标/尺寸/节奏参数 @property 曝出，改 Inspector 即生效（或刷新预览生效）。
- 每次代码交付附：改动文件清单、改动原因、用户需要做的操作（逐字段表格）；结尾固定提示"停止预览 → 重新运行验证"。
