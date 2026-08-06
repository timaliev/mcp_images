# mcp_images

MCP server for raster image manipulation — Pillow + OpenCV.

> **Requires [pi-mcp-bridge](https://github.com/timaliev/pi-mcp-bridge)** to connect to pi.

## Installation

```bash
pip install git+https://github.com/timaliev/mcp_images.git
```

Or via uv:

```bash
uv tool install git+https://github.com/timaliev/mcp_images.git
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
        "command": "mcp-raster",
        "args": []
      }
    ]
  }
}
```

### Standalone MCP client

```json
{
  "mcpServers": {
    "raster": {
      "command": "mcp-raster",
      "args": []
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `raster_info` | Image metadata: dimensions, format, mode, DPI, file size |
| `raster_convert` | Convert format (png, jpeg, webp, tiff, bmp) |
| `raster_resize` | Resize by dimensions, scale, or fit mode |
| `raster_crop` | Crop to rectangle |
| `raster_rotate` | Rotate by degrees |
| `raster_adjust` | Brightness, contrast, saturation, sharpness, gamma |
| `raster_filter` | Blur, sharpen, denoise, grayscale, invert, threshold |
| `raster_enhance` | Auto-enhance (contrast, color, sharpness, all) |

## Development

```bash
git clone https://github.com/timaliev/mcp_images.git
cd mcp_images
uv run pytest
```
