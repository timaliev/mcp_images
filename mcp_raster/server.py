"""MCP server for raster image manipulation — thin dispatch layer."""

import sys
import logging

from mcp.server import MCPServer

from mcp_raster._core import _load_image, _output_path  # kept for tool convenience
from mcp_raster.backends.pillow import PillowBackend
from mcp_raster.backends.magick import MagickBackend
from mcp_raster.draw import raster_text, raster_draw
from mcp_raster.filters import raster_filter, raster_enhance
from mcp_raster.transform import (
    raster_perspective,
    raster_morphology,
    raster_balance,
    raster_padding,
    raster_channels,
    raster_compress,
)
from mcp_raster.analysis import raster_diff, raster_histogram, raster_edge, raster_qr, raster_bgremove
from mcp_raster.metadata import raster_exif, raster_colorspace, raster_blend, raster_contours

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("mcp-images")

server = MCPServer("raster", version="0.1.0")

# ---------------------------------------------------------------------------
# Pluggable backends
# ---------------------------------------------------------------------------
_pillow = PillowBackend()
_magick = MagickBackend()
_backends = {"pillow": _pillow, "magick": _magick}


def _resolve_backend(backend_name: str | None = None) -> PillowBackend:
    """Resolve backend by name. Falls back to pillow."""
    if backend_name is None:
        return _pillow
    be = _backends.get(backend_name.lower())
    if be is None:
        return _pillow  # or could raise — but graceful fallback
    return be


# ---------------------------------------------------------------------------
# Core tools (backend-aware)
# ---------------------------------------------------------------------------

@server.tool()
def raster_info(path: str, backend: str | None = None) -> dict:
    """Return image metadata: dimensions, format, mode, DPI, file size."""
    return _resolve_backend(backend).info(path)


@server.tool()
def raster_convert(path: str, fmt: str, quality: int = 85, output: str | None = None,
                   backend: str | None = None) -> dict:
    """Convert image to another format (png, jpeg, webp, tiff, bmp)."""
    return _resolve_backend(backend).convert(path, fmt, quality, output)


@server.tool()
def raster_resize(
    path: str,
    width: int | None = None,
    height: int | None = None,
    scale: float | None = None,
    fit: str | None = None,
    output: str | None = None,
    backend: str | None = None,
) -> dict:
    """Resize image. Provide width/height, scale factor, or fit mode (cover/contain/fill)."""
    return _resolve_backend(backend).resize(path, width, height, scale, fit, output)


@server.tool()
def raster_crop(path: str, left: int, top: int, right: int, bottom: int,
                output: str | None = None, backend: str | None = None) -> dict:
    """Crop image to the specified rectangle (inclusive pixel coordinates)."""
    return _resolve_backend(backend).crop(path, left, top, right, bottom, output)


@server.tool()
def raster_rotate(path: str, degrees: float, expand: bool = True,
                  output: str | None = None, backend: str | None = None) -> dict:
    """Rotate image by degrees. expand=True enlarges canvas to fit."""
    return _resolve_backend(backend).rotate(path, degrees, expand, output)


@server.tool()
def raster_adjust(
    path: str,
    brightness: float | None = None,
    contrast: float | None = None,
    saturation: float | None = None,
    sharpness: float | None = None,
    gamma: float | None = None,
    output: str | None = None,
    backend: str | None = None,
) -> dict:
    """Adjust image properties. Values: 1.0 = no change, >1.0 = increase, <1.0 = decrease."""
    return _resolve_backend(backend).adjust(path, brightness, contrast, saturation, sharpness, gamma, output)


# ---------------------------------------------------------------------------
# Specialized tools (no backend param — Pillow/OpenCV only for now)
# ---------------------------------------------------------------------------

server.tool()(raster_exif)
server.tool()(raster_colorspace)
server.tool()(raster_blend)
server.tool()(raster_contours)

server.tool()(raster_text)
server.tool()(raster_draw)
server.tool()(raster_perspective)
server.tool()(raster_morphology)
server.tool()(raster_balance)
server.tool()(raster_padding)
server.tool()(raster_channels)
server.tool()(raster_compress)

server.tool()(raster_filter)
server.tool()(raster_enhance)

server.tool()(raster_diff)
server.tool()(raster_histogram)
server.tool()(raster_edge)
server.tool()(raster_qr)
server.tool()(raster_bgremove)


def main():
    import sys
    if "--version" in sys.argv:
        from importlib.metadata import version
        print(f"mcp-images {version('mcp-images')}")
        return
    server.run()


if __name__ == "__main__":
    main()
