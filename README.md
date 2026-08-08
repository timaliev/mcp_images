# mcp_images

MCP server for raster image manipulation — Pillow + OpenCV. 24 tools across draw, filter, transform, metadata, and analysis categories.

> **Requires [pi-mcp-bridge](https://github.com/timaliev/pi-mcp-bridge)** to connect to [pi](https://pi.dev).

## Installation

```bash
pip install git+https://github.com/timaliev/mcp_images.git
```

Or via uv:

```bash
uv tool install git+https://github.com/timaliev/mcp_images.git
# with analysis extras (diff, qr, bgremove):
uv tool install git+https://github.com/timaliev/mcp_images.git[mcp-images]
pip install mcp-images[analysis]
```

## Configuration

### With pi-mcp-bridge

In `~/.pi/agent/settings.json`:

```json
{
  "mcpBridge": {
    "servers": [
      {
        "name": "raster",
        "command": "mcp-images",
        "args": []
      }
    ]
  }
}
```

### Standalone MCP client

In `~/.mcp.json`:

```json
{
  "mcpServers": {
    "raster": {
      "command": "mcp-images",
      "args": []
    }
  }
}
```

## Tools (24 total)

### Core
| Tool | Description |
|------|-------------|
| `raster_info` | Image metadata: dimensions, format, mode, DPI, file size |
| `raster_convert` | Convert format (png, jpeg, webp, tiff, bmp). Use `fmt` parameter |
| `raster_resize` | Resize by dimensions, scale, or fit mode |
| `raster_crop` | Crop to rectangle |
| `raster_rotate` | Rotate by degrees |
| `raster_adjust` | Brightness, contrast, saturation, sharpness, gamma |

### Draw
| Tool | Description |
|------|-------------|
| `raster_text` | Overlay text with font size and color |
| `raster_draw` | Draw shapes: rect, circle, line, arrow |

### Filters
| Tool | Description |
|------|-------------|
| `raster_filter` | Blur, sharpen, denoise, grayscale, invert, threshold. Use `filter_name` |
| `raster_enhance` | Auto-enhance: contrast, color, sharpness, all |

### Transform
| Tool | Description |
|------|-------------|
| `raster_perspective` | 4-point perspective correction |
| `raster_morphology` | Morphological ops: dilate, erode, open, close |
| `raster_balance` | Auto balance: equalize, autocontrast, auto white |
| `raster_padding` | Add border/margin with fill color |
| `raster_channels` | Channel ops: extract, swap, reorder |
| `raster_compress` | Compress: quality control, metadata stripping |

### Metadata
| Tool | Description |
|------|-------------|
| `raster_exif` | Extract EXIF metadata as dict |
| `raster_colorspace` | Convert: RGB, HSV, LAB, grayscale |
| `raster_blend` | Alpha-blend two images |
| `raster_contours` | Find contours with OpenCV, draw on output |

### Analysis (requires `pip install mcp-images[analysis]`)
| Tool | Description |
|------|-------------|
| `raster_diff` | SSIM structural similarity between two images |
| `raster_histogram` | Channel histogram (R/G/B/all) |
| `raster_edge` | Canny edge detection |
| `raster_qr` | Decode QR codes and barcodes |
| `raster_bgremove` | Remove background (returns RGBA) |

## Development

```bash
git clone https://github.com/timaliev/mcp_images.git
cd mcp_images
uv run pytest
```
