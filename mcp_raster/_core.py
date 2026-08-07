"""Shared utilities for raster MCP tools."""

import os
import tempfile
from pathlib import Path
from PIL import Image

OUTPUT_DIR = Path(os.environ.get("RASTER_OUTPUT_DIR", tempfile.gettempdir()))


def _output_path(path: str, suffix: str | None = None) -> str:
    """Generate output path, preserving original extension with optional suffix before it."""
    p = Path(path)
    stem = p.stem
    ext = p.suffix
    suffix_str = f"_{suffix}" if suffix else ""
    out = OUTPUT_DIR / f"{stem}__processed{suffix_str}{ext}"
    counter = 1
    while out.exists():
        out = OUTPUT_DIR / f"{stem}__processed{suffix_str}_{counter}{ext}"
        counter += 1
    return str(out)


def _load_image(path: str) -> tuple[Image.Image | None, dict | None]:
    """Load image or return structured error dict."""
    if not os.path.isfile(path):
        return None, {"success": False, "error": "ENOENT", "detail": f"File not found: {path}"}
    try:
        return Image.open(path), None
    except Exception as e:
        return None, {"success": False, "error": "EPROCESSING", "detail": f"Cannot open image: {e}"}
