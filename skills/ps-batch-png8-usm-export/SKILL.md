---
name: ps-batch-png8-usm-export
agent_created: true
description: Batch compress PNG atlases by opening them in Photoshop, applying Unsharp Mask, and re-exporting as 8-bit PNG ("较小文件" / PNG-8) via the photoshop MCP server. Use when the user wants to reduce PNG file size for game sprite atlases or UI assets while keeping transparency.
---

# Photoshop Batch PNG-8 USM Export

## Overview

This skill automates a common game-asset optimization workflow: take a folder of PNG files (typically sprite atlases ending in `_atlas_4x4.png` or similar), open each one in Photoshop, apply a gentle Unsharp Mask (USM), and re-export as an 8-bit PNG using Photoshop's "较小文件 (8位)" / PNG-8 Save-for-Web mode. The result keeps transparency and is dramatically smaller than the original 24/32-bit PNG.

## When to use

- User has a folder of large transparent PNG atlases that need smaller file sizes.
- The source filenames contain a predictable pattern such as `_atlas_4x4`.
- Photoshop 2021+ is installed and reachable via the `@alisaitteke/photoshop-mcp` MCP server.
- The goal is lossy-but-clean compression suitable for mobile game assets.

## Requirements

- Photoshop MCP server is installed and trusted in WorkBuddy (`~/.workbuddy/mcp.json`).
- Photoshop is running.
- `PHOTOSHOP_PATH` is set in the MCP env if Photoshop is not in the default location.
- Output folder must be writable (the script creates it automatically).

## Workflow

1. **Discover files**: Glob the source folder for files matching the requested pattern (e.g. `**/*_atlas_4x4.png`). Note: Glob may miss files with Chinese folder names — fall back to `ls` via Bash to enumerate the real file list.
2. **Prepare output directory**: Create a sibling folder such as `<source>/exported_8bit` or any path the user specifies.
3. **Verify connection**: Run `photoshop_ping` once. Also confirm the target folder actually exists and list its files before assuming the Globs worked.
4. **Process in small batches**: Send ExtendScript batches of **2-3 files per call** to Photoshop via `mcp__photoshop__photoshop_execute_script`. Do NOT send parallel JSX calls — Photoshop processes one batch at a time.
5. **Log per file, append immediately**: Inside the JSX loop, after each file's export succeeds or fails, append one TSV line to `batch_log_N.txt` with `File.open('a')` right away. Do NOT buffer the whole batch and write once at the end — if the script times out mid-batch, buffered logs are lost while already-exported files are fine.
6. **Verify each batch**: Read the `batch_log_N.txt` after every batch to confirm all rows are `ok`. If a batch timed out, the completed files are already exported; just re-run the remaining files in a new batch.
7. **Summarize**: After all batches, count output files and compute total compression ratio (source bytes vs output bytes).

## Parameters to decide with the user

- Source folder and file pattern.
- Output folder (default: `<source>/exported_8bit` with mirrored subfolders).
- USM settings: default is `amount=100`, `radius=1.0px`, `threshold=0`. Adjust if the user asks for more/less sharpening.
- **Resize scale (optional)**: default `1.0` (no resize). If the user asks to "shrink to 50%" / "缩小到50%", set `0.5`. Apply resize BEFORE USM, then export. Order matters: `doc.resizeImage(newW, newH, 72, ResampleMethod.BICUBICSHARPER)` → `applyUnSharpMask(...)` → PNG-8 export. Resizing first then sharpening compensates the blur introduced by downscaling.
- Whether to overwrite existing output files (current behavior: yes, because export overwrites).

## Known constraints

- The MCP `photoshop_export_as` tool does **not** expose the "较小文件 (8位)" checkbox, so this skill falls back to `photoshop_execute_script` with `ExportOptionsSaveForWeb` and `opts.PNG8 = true`.
- `photoshop_execute_script` reliably executes the JSX but its return value often serializes as `undefined`; rely on filesystem checks and batch logs instead.
- **Single-script timeout**: `photoshop_execute_script` has a hard timeout. Sending 3+ files in one batch can time out on the last file. If the log is written only at the end, all progress for that batch is lost. Workaround: process 2-3 files per batch AND append the log line per file (see Example). Already-exported files survive a timeout; just re-run the failed batch.
- Photoshop processes one batch at a time; do not send parallel JSX calls.
- PNG-8 is 256-color. Images with heavy gradients or small text may show slight banding/aliasing. If that happens, switch to PNG-24 or adjust USM and re-run.

## Example JSX snippet

```jsx
(function() {
  app.displayDialogs = DialogModes.NO;
  var files = [ /* absolute paths */ ];
  var logPath = '/source_folder/exported_8bit/batch_log_N.txt';
  for (var i = 0; i < files.length; i++) {
    var srcPath = files[i];
    var outPath = srcPath.replace('/source_folder/', '/source_folder/exported_8bit/');
    var srcFile = new File(srcPath);
    var outFile = new File(outPath);
    outFile.parent.create();
    var status = 'ok', error = '', srcSize = srcFile.length, outSize = 0;
    try {
      var doc = app.open(srcFile);
      doc.activeLayer.applyUnSharpMask(100, 1.0, 0);
      var opts = new ExportOptionsSaveForWeb();
      opts.format = SaveDocumentType.PNG;
      opts.PNG8 = true;
      opts.transparency = true;
      opts.interlaced = false;
      doc.exportDocument(outFile, ExportType.SAVEFORWEB, opts);
      doc.close(SaveOptions.DONOTSAVECHANGES);
      outSize = outFile.length;
    } catch (e) {
      status = 'error';
      error = e.toString().replace(/\t/g, ' ').replace(/\n/g, ' ');
    }
    // Append log IMMEDIATELY so a mid-batch timeout does not lose completed work
    var lf = new File(logPath);
    lf.encoding = 'UTF-8';
    lf.open('a');
    if (lf.length === 0) lf.writeln('status\tsource\toutput\tsourceSize\toutputSize\terror');
    lf.writeln([status, srcPath, outPath, srcSize, outSize, error].join('\t'));
    lf.close();
  }
  return 'done';
})();
```

### Resize variant (shrink before export)

When the user wants the output also downscaled (e.g. "缩小到 50%"), inside the `try` block resize first, then sharpen, then export. Use `BICUBICSHARPER` for downscale + follow-up sharpen:

```jsx
      var doc = app.open(srcFile);
      var srcW = doc.width.as('px'), srcH = doc.height.as('px');
      var newW = Math.round(srcW * 0.5), newH = Math.round(srcH * 0.5);
      doc.resizeImage(UnitValue(newW, 'px'), UnitValue(newH, 'px'), 72, ResampleMethod.BICUBICSHARPER);
      doc.activeLayer.applyUnSharpMask(100, 1.0, 0);
      // ... then exportDocument with PNG8 opts as above
```

Log `srcW/srcH/outW/outH` too so you can verify the scale took effect. Always resize BEFORE USM so the sharpen compensates the blur from downscaling.
