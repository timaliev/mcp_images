# mcp_images

MCP server for raster image manipulation — Pillow + OpenCV. 25 tools across draw, filter, transform, metadata, and analysis categories.

> **Requires [pi-mcp-bridge](https://github.com/timaliev/pi-mcp-bridge)** to connect to [pi](https://pi.dev).

## Installation

```bash
# Base install (Pillow + ImageMagick/Wand)
pip install git+https://github.com/timaliev/mcp_images.git

# Or via uv:
uv tool install git+https://github.com/timaliev/mcp_images.git
```

### Optional dependencies

| Extra | Packages | Tools enabled |
|-------|----------|---------------|
| `[analysis]` | scikit-image, pyzbar, rembg | `raster_diff`, `raster_qr`, `raster_bgremove` |

```bash
# With analysis extras:
pip install "git+https://github.com/timaliev/mcp_images.git#egg=mcp-images[analysis]"

# Or via uv:
uv tool install "git+https://github.com/timaliev/mcp_images.git#egg=mcp-images[analysis]"
```

ImageMagick must be installed separately via system package manager:
```bash
brew install imagemagick          # macOS
apt install imagemagick           # Debian/Ubuntu
```

## Configuration

### With pi-mcp-bridge

First install pi-mcp-bridge:

```bash
pi add mcp-bridge
# or manually:
# git clone https://github.com/timaliev/pi-mcp-bridge ~/.pi/agent/extensions/pi-mcp-bridge
```

Then configure mcp-images in `~/.pi/agent/settings.json`:

```json
{
  "mcpBridge": {
    "servers": [
      {
        "name": "raster",
        "command": "mcp-images",
        "args": [],
        "setupCommands": [
          "uv tool install --force --python 3.11 \"mcp-images[analysis] @ git+https://github.com/timaliev/mcp_images.git\""
        ]
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

## Backends

Core tools accept an optional `backend` parameter (`"pillow"` or `"magick"`).

| Backend | Library | Strengths |
|---------|---------|-----------|
| `pillow` (default) | Pillow + OpenCV | Fast, simple, no extra deps |
| `magick` | Wand / ImageMagick | HEIC/AVIF/GIF, 40+ resize filters, industry-standard unsharp mask |

```
# Use ImageMagick for HEIC conversion
raster_convert(path, "heic", backend="magick")

# Mitchell filter resize via ImageMagick
raster_resize(path, width=800, backend="magick")

# Back to Pillow for speed
raster_crop(path, 10, 10, 100, 100, backend="pillow")
```

## Tools (25 total)

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
