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

1. **Discover files**: Glob the source folder for files matching the requested pattern (e.g. `**/*_atlas_4x4.png`).
2. **Prepare output directory**: Create a sibling folder such as `<source>/exported_8bit` or any path the user specifies.
3. **Process in small batches**: Send ExtendScript batches (2-5 files per call) to Photoshop via `mcp__photoshop__photoshop_execute_script`.
4. **Per-file operations inside the JSX**:
   - Open the source PNG: `var doc = app.open(new File(srcPath));`
   - Apply Unsharp Mask to the active raster layer: `doc.activeLayer.applyUnSharpMask(100, 1.0, 0);`
   - Create output folder: `outFile.parent.create();`
   - Configure Save-for-Web PNG-8 export:
     ```jsx
     var opts = new ExportOptionsSaveForWeb();
     opts.format = SaveDocumentType.PNG;
     opts.PNG8 = true;
     opts.transparency = true;
     opts.interlaced = false;
     doc.exportDocument(outFile, ExportType.SAVEFORWEB, opts);
     ```
   - Close without saving changes to the original: `doc.close(SaveOptions.DONOTSAVECHANGES);`
5. **Log per file**: Record source path, output path, source bytes, output bytes, and any error.
6. **Verify**: After all batches finish, count output files and compute total compression ratio.

## Parameters to decide with the user

- Source folder and file pattern.
- Output folder (default: `<source>/exported_8bit` with mirrored subfolders).
- USM settings: default is `amount=100`, `radius=1.0px`, `threshold=0`. Adjust if the user asks for more/less sharpening.
- Whether to overwrite existing output files (current behavior: yes, because export overwrites).

## Known constraints

- The MCP `photoshop_export_as` tool does **not** expose the "较小文件 (8位)" checkbox, so this skill falls back to `photoshop_execute_script` with `ExportOptionsSaveForWeb` and `opts.PNG8 = true`.
- `photoshop_execute_script` reliably executes the JSX but its return value may serialize as `undefined`; rely on filesystem checks and batch logs instead.
- Photoshop processes one batch at a time; do not send parallel JSX calls.

## Example JSX snippet

```jsx
(function() {
  app.displayDialogs = DialogModes.NO;
  var files = [ /* absolute paths */ ];
  for (var i = 0; i < files.length; i++) {
    var srcPath = files[i];
    var outPath = srcPath.replace('/source_folder/', '/source_folder/exported_8bit/');
    var srcFile = new File(srcPath);
    var outFile = new File(outPath);
    outFile.parent.create();
    var doc = app.open(srcFile);
    doc.activeLayer.applyUnSharpMask(100, 1.0, 0);
    var opts = new ExportOptionsSaveForWeb();
    opts.format = SaveDocumentType.PNG;
    opts.PNG8 = true;
    opts.transparency = true;
    opts.interlaced = false;
    doc.exportDocument(outFile, ExportType.SAVEFORWEB, opts);
    doc.close(SaveOptions.DONOTSAVECHANGES);
  }
  return 'done';
})();
```
