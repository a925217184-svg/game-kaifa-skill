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
