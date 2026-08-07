"""Filter and enhance tools for raster MCP."""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from mcp_raster._core import _load_image, _output_path

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


def raster_filter(
    path: str,
    filter_name: str,
    radius: int = 2,
    threshold_value: int = 128,
    output: str | None = None,
) -> dict:
    """Apply a named filter. Supported: blur, gaussian_blur, median, sharpen, edge_enhance, denoise, grayscale, invert, threshold."""
    img, err = _load_image(path)
    if err:
        return err
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


def raster_enhance(path: str, mode: str = "all", factor: float = 1.5, output: str | None = None) -> dict:
    """Auto-enhance image. mode: contrast, color, sharpness, or all."""
    img, err = _load_image(path)
    if err:
        return err
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
