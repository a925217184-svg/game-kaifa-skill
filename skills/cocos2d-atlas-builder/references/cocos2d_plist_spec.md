# Cocos2d .plist 规范（Free Texture Packer 对齐）

本文件记录从 Free Texture Packer（FTP）的 `Cocos2d` 导出模板反向学习得到的
要点，以及本技能 `gen_plist.py` 为何这样写。Cocos Creator / cocos2d-x 的
plist 解析器对格式非常敏感，任意偏差都会让导入时报错（典型的运行时异常：
`Cannot read properties of undefined (reading 'slice'/'indexes')`）。

## 关键字段（缺一不可）

| 字段 | 正确值 | 常见错误 |
|------|--------|----------|
| DOCTYPE | `-//Apple Computer//DTD PLIST 1.0//EN` | 用 `-//Apple//DTD PLIST 1.0//EN`（少 `Computer`） |
| `metadata.format` | `<integer>2</integer>` | 写成 `3` |
| `metadata.pixelFormat` | `<string>RGBA8888</string>` | 缺失或写错 |
| `metadata.premultiplyAlpha` | `<false/>` | 写成 `premultipliedAlpha`（key 名错） |
| 缩进 | 2 空格 | 4 空格 / tab（部分解析器仍接受，但保持 2 空格最稳） |

## rect / offset / size 字符串严禁空格

Cocos 用正则提取 `{{x,y},{w,h}}`。**任何空格都会让正则失败**：

- ✅ `{{0,0},{256,256}}`
- ❌ `{{0, 0},{256, 256}}`

`gen_plist.py` 中对所有数值字段统一 `replace(" ", "")`，确保零空格。

## 帧字段结构

每个 frame 必须包含（顺序无关，但 key 必须存在）：

- `frame` → `{{x,y},{w,h}}`：精灵在图集中的像素矩形（左上原点）
- `offset` → `{0,0}`（本工作流不偏移）
- `rotated` → `<false/>` 或 `<true/>`
- `sourceColorRect` → `{{0,0},{w,h}}`
- `sourceSize` → `{w,h}`

## 与 libGDX .atlas 的映射

`build_atlas.py` 产出的 `.atlas`（libGDX 风格）字段到 plist 的映射：

- `xy: x, y`   → `frame` 的 `{x,y}`
- `size: w, h` → `frame` 的 `{w,h}` 与 `sourceColorRect` / `sourceSize`
- `orig: w, h` → `sourceSize`
- `offset: 0, 0` → `offset`
- `rotate`     → `rotated`

## 自检

`gen_plist.py` 在写盘后用 `plistlib.loads` 重新解析，输出 `OK` 或
`PARSE-FAIL` 立即暴露格式错误，避免把坏文件喂给 Cocos。

## 失败案例回顾（本技能来源）

1. 原脚本 rect 字符串带空格 + `size` 无花括号 → Cocos 解析抛 `slice` 异常。
2. 错误的 DOCTYPE / `format=3` / `premultipliedAlpha` → 导入失败。
3. 修改后严格对齐 FTP 模板（format=2, RGBA8888, premultiplyAlpha, 2 空格缩进,
   无空格 rect），Cocos 正常加载。

## TexturePacker `cocos2d` 导出格式（format=3，工具生成）

走 TexturePacker CLI（`--format cocos2d`，见 SKILL.md 的 Workflow B）生成的 plist
与手动 `gen_plist.py`（format=2）**结构不同**，但 Cocos Creator 都能导入。
**不要把它"修"成 format=2**——TexturePacker 的 format=3 是它的标准输出。

### 帧字段结构（用 `textureRect` 而非 `frame`）

```
<key>frames</key>
<dict>
  <key>name_00</key>
  <dict>
    <key>aliases</key>        <array/>
    <key>spriteOffset</key>   <string>{0,0}</string>
    <key>spriteSize</key>     <string>{240,240}</string>
    <key>spriteSourceSize</key> <string>{240,240}</string>
    <key>textureRect</key>    <string>{{6,6},{240,240}}</string>
    <key>textureRotated</key> <false/>
  </dict>
  ...
</dict>
<key>metadata</key>
<dict>
  <key>format</key>            <integer>3</integer>
  <key>pixelFormat</key>      <string>RGBA8888</string>
  <key>premultiplyAlpha</key>  <false/>
  <key>size</key>             <string>{1024,1024}</string>
  ...
</dict>
```

### 解析时的坑（已踩过）
- 读每帧矩形要用 **`textureRect`**，不是 `frame`；旋转标志用 **`textureRotated`**，
  不是 `rotated`。手动 `gen_plist.py` 用的是 `frame`/`rotated`，两套 plist 字段名不同，
  切换解析器时务必对齐。
- `textureRect` 同样是 `{{x,y},{w,h}}`，但原点是**左上**（Cocos y-down），无需做
  y-up 翻转（与手动 `gen_plist.py` 在行优先网格里需要 `y=(H-cell)-r*cell` 的处理相反，
  因为那是手动写入的约定，TP 已经按 Coco s坐标系写好了）。
- `spriteSize` / `spriteSourceSize` 都是 `{w,h}`（注意是花括号，不是 rect 的 `{{}}`）。
- 网格布局：用 `--algorithm Grid` + `--shape-padding 4` + `--border-padding 4` +
  `--extrude 2` 时，相邻帧之间会有 ≥8px 透明 gutter，相邻帧矩形互不重叠，可直接按
  `textureRect` 切片，绝不会切到邻帧。
- 若需逐帧按数字排序播放，key 形如 `name_00..name_15`，按末尾两位数字排序即可。
