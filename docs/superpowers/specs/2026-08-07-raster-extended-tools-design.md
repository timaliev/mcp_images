# Raster MCP — Extended Image Manipulation Tools

**Date:** 2026-08-07  
**Status:** Approved

## Overview

Add 17 new raster manipulation tools + restructure existing code into modules.
All open-source (Pillow/OpenCV/scikit-image/pyzbar/rembg), MIT/Apache licensed.

## Architecture

```
mcp_raster/
├── __init__.py
├── server.py          # orchestration: imports modules, registers all tools
├── _core.py           # _load_image, _output_path (shared utilities, moved from server.py)
├── draw.py            # raster_text, raster_draw
├── analysis.py        # raster_diff, raster_histogram, raster_edge, raster_qr, raster_bgremove
├── transform.py       # raster_perspective, raster_morphology, raster_balance,
│                      #   raster_padding, raster_channels, raster_compress
├── metadata.py        # raster_exif, raster_colorspace, raster_blend, raster_contours
└── filters.py         # raster_filter, raster_enhance (moved from server.py)
```

Existing 7 tools (`raster_info`, `raster_convert`, `raster_resize`, `raster_crop`,
`raster_rotate`, `raster_adjust`, and the moved `raster_filter`/`raster_enhance`)
remain in `server.py` or move to modules.

Each module 50-150 lines. Testable independently. Same Pillow/OpenCV deps as before.

## Tools

### Draw

| Tool | Lib | Description |
|------|-----|-------------|
| `raster_text` | Pillow ImageDraw | Overlay text at position with font size and color |
| `raster_draw` | Pillow ImageDraw | Draw shapes: rect, circle, line, arrow |

### Analysis (needs `[analysis]` extras)

| Tool | Lib | Description |
|------|-----|-------------|
| `raster_diff` | scikit-image SSIM | Structural similarity between two images, returns score + diff image |
| `raster_histogram` | Pillow | Channel histogram (R/G/B/all) |
| `raster_edge` | OpenCV Canny | Edge detection with low/high thresholds |
| `raster_qr` | pyzbar | Decode QR codes and barcodes, returns text list |
| `raster_bgremove` | rembg | Remove background from image |

### Transform

| Tool | Lib | Description |
|------|-----|-------------|
| `raster_perspective` | OpenCV | 4-point perspective correction for document scanning |
| `raster_morphology` | OpenCV | Dilate, erode, open, close operations |
| `raster_balance` | Pillow ImageOps | Auto white balance, histogram equalization |
| `raster_padding` | Pillow ImageOps.expand | Add border/margin with fill color |
| `raster_channels` | Pillow split/merge | Extract, swap, or reorder color channels |
| `raster_compress` | Pillow optimize | Compress with quality control, strip metadata |

### Metadata

| Tool | Lib | Description |
|------|-----|-------------|
| `raster_exif` | Pillow getexif() | Extract EXIF metadata as dict |
| `raster_colorspace` | Pillow convert() | Convert between RGB, HSV, LAB, grayscale |
| `raster_blend` | Pillow Image.blend() | Alpha-blend two images |
| `raster_contours` | OpenCV findContours | Find contours, filter by area |

## Dependencies

```toml
[project.optional-dependencies]
analysis = ["scikit-image>=0.24", "pyzbar>=0.1", "rembg>=2.0"]
```

Base deps unchanged: `pillow>=11.0`, `opencv-python-headless>=4.10`, `mcp[cli]>=1.9`.

Lazy imports: each analysis tool imports its extra dep inside the function.
Missing dep → `{"success": False, "error": "EUNSUPPORTED", "detail": "Install: pip install mcp-images[analysis]"}`.

## Error Handling

All tools follow existing pattern: `img, err = _load_image(path); if err: return err`.
Structured errors with ENOENT/EPROCESSING/EUNSUPPORTED codes.

## Testing

One test file per module in `tests/`: `test_draw.py`, `test_analysis.py`, `test_transform.py`,
`test_metadata.py`. Tests for optional-dep tools skip gracefully if deps not installed.
Existing `test_server.py` stays.

Target: 2+ tests per tool. All tests <5s total suite time.

## Implementation Order

1. `_core.py` — extract shared utilities
2. `metadata.py` — simplest, no new deps (exif, colorspace, blend)
3. `filters.py` — move existing, no new deps
4. `draw.py` — text + shapes, no new deps
5. `transform.py` — perspective, morphology, balance, padding, channels, compress
6. `analysis.py` — diff, histogram, edge, qr, bgremove (needs extras)
7. `server.py` — wire up, update README
