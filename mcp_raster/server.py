"""MCP server for raster image manipulation using Pillow + OpenCV."""

import os
import sys
import logging

from mcp.server import MCPServer
from PIL import Image, ImageEnhance
import cv2
import numpy as np

from mcp_raster._core import _load_image, _output_path
from mcp_raster.filters import raster_filter, raster_enhance

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("mcp-raster")

server = MCPServer("raster", version="0.1.0")


@server.tool()
def raster_info(path: str) -> dict:
    """Return image metadata: dimensions, format, mode, DPI, file size."""
    img, err = _load_image(path)
    if err:
        return err
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
    img, err = _load_image(path)
    if err:
        return err
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
    img, err = _load_image(path)
    if err:
        return err

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
    img, err = _load_image(path)
    if err:
        return err
    cropped = img.crop((left, top, right, bottom))
    out = output or _output_path(path, "crop")
    cropped.save(out)
    return {"success": True, "output_path": out, "crop_rect": [left, top, right, bottom]}


@server.tool()
def raster_rotate(path: str, degrees: float, expand: bool = True, output: str | None = None) -> dict:
    """Rotate image by degrees. expand=True enlarges canvas to fit."""
    img, err = _load_image(path)
    if err:
        return err
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
    img, err = _load_image(path)
    if err:
        return err

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





def main():
    server.run()


if __name__ == "__main__":
    main()
