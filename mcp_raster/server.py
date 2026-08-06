"""MCP server for raster image manipulation using Pillow + OpenCV."""

import os
import sys
import tempfile
import logging
from pathlib import Path

from mcp.server import MCPServer
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import cv2
import numpy as np

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("mcp-raster")

server = MCPServer("raster", version="0.1.0")
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


def _load_image(path: str) -> Image.Image:
    """Load image or raise structured error if not found."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")
    return Image.open(path)


@server.tool()
def raster_info(path: str) -> dict:
    """Return image metadata: dimensions, format, mode, DPI, file size."""
    img = _load_image(path)
    return {
        "success": True,
        "width": img.width,
        "height": img.height,
        "format": img.format,
        "mode": img.mode,
        "dpi": img.info.get("dpi"),
        "filesize": os.path.getsize(path),
        "channels": len(img.getbands()),
    }


@server.tool()
def raster_convert(path: str, fmt: str, quality: int = 85, output: str | None = None) -> dict:
    """Convert image to another format (png, jpeg, webp, tiff, bmp)."""
    img = _load_image(path)
    fmt = fmt.lower()
    if fmt not in {"png", "jpeg", "webp", "tiff", "bmp"}:
        return {"success": False, "error": "EUNSUPPORTED", "detail": f"Unsupported format: {fmt}"}

    out = output or _output_path(path, fmt if fmt != "jpeg" else "jpg")
    save_kwargs = {}
    if fmt == "jpeg":
        save_kwargs["quality"] = quality
    elif fmt == "webp":
        save_kwargs["quality"] = quality

    if fmt == "jpeg" and img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.save(out, format=fmt.upper(), **save_kwargs)
    return {"success": True, "output_path": out, "format": fmt, "size": os.path.getsize(out)}


@server.tool()
def raster_resize(
    path: str,
    width: int | None = None,
    height: int | None = None,
    scale: float | None = None,
    fit: str | None = None,
    output: str | None = None,
) -> dict:
    """Resize image. Provide width/height, scale factor, or fit mode (cover/contain/fill)."""
    img = _load_image(path)

    if scale and width is None and height is None:
        width = int(img.width * scale)
        height = int(img.height * scale)

    if fit and width and height:
        if fit == "contain":
            img.thumbnail((width, height), Image.LANCZOS)
        elif fit == "cover":
            ratio = max(width / img.width, height / img.height)
            new_w = int(img.width * ratio)
            new_h = int(img.height * ratio)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            left = (new_w - width) // 2
            top = (new_h - height) // 2
            img = img.crop((left, top, left + width, top + height))
        elif fit == "fill":
            img = img.resize((width, height), Image.LANCZOS)
    elif width and height:
        img = img.resize((width, height), Image.LANCZOS)
    elif width:
        ratio = width / img.width
        img = img.resize((width, int(img.height * ratio)), Image.LANCZOS)
    elif height:
        ratio = height / img.height
        img = img.resize((int(img.width * ratio), height), Image.LANCZOS)

    out = output or _output_path(path)
    img.save(out)
    return {"success": True, "output_path": out, "width": img.width, "height": img.height}


@server.tool()
def raster_crop(path: str, left: int, top: int, right: int, bottom: int, output: str | None = None) -> dict:
    """Crop image to the specified rectangle (inclusive pixel coordinates)."""
    img = _load_image(path)
    cropped = img.crop((left, top, right, bottom))
    out = output or _output_path(path, "crop")
    cropped.save(out)
    return {"success": True, "output_path": out, "crop_rect": [left, top, right, bottom]}


@server.tool()
def raster_rotate(path: str, degrees: float, expand: bool = True, output: str | None = None) -> dict:
    """Rotate image by degrees. expand=True enlarges canvas to fit."""
    img = _load_image(path)
    rotated = img.rotate(degrees, expand=expand, resample=Image.BICUBIC)
    out = output or _output_path(path)
    rotated.save(out)
    return {"success": True, "output_path": out}


@server.tool()
def raster_adjust(
    path: str,
    brightness: float | None = None,
    contrast: float | None = None,
    saturation: float | None = None,
    sharpness: float | None = None,
    gamma: float | None = None,
    output: str | None = None,
) -> dict:
    """Adjust image properties. Values: 1.0 = no change, >1.0 = increase, <1.0 = decrease."""
    img = _load_image(path)

    if brightness is not None:
        img = ImageEnhance.Brightness(img).enhance(brightness)
    if contrast is not None:
        img = ImageEnhance.Contrast(img).enhance(contrast)
    if saturation is not None:
        img = ImageEnhance.Color(img).enhance(saturation)
    if sharpness is not None:
        img = ImageEnhance.Sharpness(img).enhance(sharpness)
    if gamma is not None:
        arr = np.array(img)
        lut = np.array([((i / 255.0) ** (1.0 / gamma)) * 255 for i in range(256)]).astype(np.uint8)
        arr = cv2.LUT(arr, lut)
        img = Image.fromarray(arr)

    out = output or _output_path(path)
    img.save(out)
    return {"success": True, "output_path": out}


_FILTERS = {
    "blur": ImageFilter.BLUR,
    "sharpen": ImageFilter.SHARPEN,
    "edge_enhance": ImageFilter.EDGE_ENHANCE,
    "grayscale": "grayscale",
    "invert": "invert",
    "threshold": "threshold",
    "denoise": "denoise",
    "gaussian_blur": "gaussian_blur",
    "median": "median",
}


@server.tool()
def raster_filter(
    path: str,
    filter_name: str,
    radius: int = 2,
    threshold_value: int = 128,
    output: str | None = None,
) -> dict:
    """Apply a named filter. Supported: blur, gaussian_blur, median, sharpen, edge_enhance, denoise, grayscale, invert, threshold."""
    img = _load_image(path)
    fname = filter_name.lower()

    if fname not in _FILTERS:
        return {
            "success": False,
            "error": "EUNSUPPORTED",
            "detail": f"Unknown filter: {filter_name}. Available: {', '.join(_FILTERS)}",
        }

    if fname == "grayscale":
        img = ImageOps.grayscale(img)
    elif fname == "invert":
        img = ImageOps.invert(img.convert("RGB"))
    elif fname == "threshold":
        gray = img.convert("L")
        img = gray.point(lambda p: 255 if p > threshold_value else 0)
    elif fname == "denoise":
        arr = np.array(img.convert("RGB"))
        arr = cv2.fastNlMeansDenoisingColored(arr, None, h=10, hColor=10, templateWindowSize=7, searchWindowSize=21)
        img = Image.fromarray(arr)
    elif fname == "gaussian_blur":
        img = img.filter(ImageFilter.GaussianBlur(radius=radius))
    elif fname == "median":
        img = img.filter(ImageFilter.MedianFilter(size=radius))
    else:
        img = img.filter(_FILTERS[fname])

    out = output or _output_path(path, filter_name)
    img.save(out)
    return {"success": True, "output_path": out, "filter_applied": filter_name}


@server.tool()
def raster_enhance(path: str, mode: str = "all", factor: float = 1.5, output: str | None = None) -> dict:
    """Auto-enhance image. mode: contrast, color, sharpness, or all."""
    img = _load_image(path)
    modes = {"contrast": False, "color": False, "sharpness": False}

    if mode == "all":
        modes = {"contrast": True, "color": True, "sharpness": True}
    elif mode in modes:
        modes[mode] = True
    else:
        return {"success": False, "error": "EUNSUPPORTED", "detail": f"Unknown mode: {mode}"}

    if modes["contrast"]:
        img = ImageEnhance.Contrast(img).enhance(factor)
    if modes["color"]:
        img = ImageEnhance.Color(img).enhance(factor)
    if modes["sharpness"]:
        img = ImageEnhance.Sharpness(img).enhance(factor)

    out = output or _output_path(path, "enhanced")
    img.save(out)
    return {"success": True, "output_path": out}


def main():
    server.run()


if __name__ == "__main__":
    main()
