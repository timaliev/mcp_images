"""Metadata tools for raster MCP: EXIF, colorspace, blend, contours."""

import os
import cv2
import numpy as np
from PIL import Image

from mcp_raster._core import _load_image, _output_path


def raster_exif(path: str) -> dict:
    """Extract EXIF metadata as a dict."""
    img, err = _load_image(path)
    if err:
        return err
    exif_data = {}
    try:
        exif = img.getexif()
        if exif:
            for tag_id, value in exif.items():
                from PIL.ExifTags import TAGS
                tag_name = TAGS.get(tag_id, str(tag_id))
                if isinstance(value, bytes):
                    value = value.decode("utf-8", errors="replace")
                exif_data[tag_name] = str(value) if not isinstance(value, (int, float)) else value
    except Exception:
        pass
    return {"success": True, "exif": exif_data}


_COLORSPACES = {"RGB", "HSV", "LAB", "L", "YCbCr"}


def raster_colorspace(path: str, target: str, output: str | None = None) -> dict:
    """Convert image to another colorspace. Supported: RGB, HSV, LAB, L (grayscale)."""
    img, err = _load_image(path)
    if err:
        return err
    cs = target.upper()
    if cs not in _COLORSPACES:
        return {"success": False, "error": "EUNSUPPORTED",
                "detail": f"Unknown colorspace: {target}. Available: {', '.join(sorted(_COLORSPACES))}"}
    try:
        converted = img.convert(cs)
    except ValueError as e:
        return {"success": False, "error": "EPROCESSING", "detail": str(e)}
    # Convert back to RGB for saving (PNG doesn't support HSV/LAB)
    if converted.mode not in ("RGB", "L", "RGBA"):
        converted = converted.convert("RGB")
    out = output or _output_path(path, cs.lower())
    converted.save(out)
    return {"success": True, "output_path": out, "colorspace": cs}


def raster_blend(path1: str, path2: str, alpha: float = 0.5, output: str | None = None) -> dict:
    """Alpha-blend two images of same size."""
    img1, err = _load_image(path1)
    if err:
        return err
    img2, err2 = _load_image(path2)
    if err2:
        return err2
    if img1.size != img2.size:
        img2 = img2.resize(img1.size, Image.LANCZOS)
    blended = Image.blend(img1.convert("RGB"), img2.convert("RGB"), alpha)
    out = output or _output_path(path1, "blended")
    blended.save(out)
    return {"success": True, "output_path": out, "alpha": alpha}


def raster_contours(path: str, threshold: int = 128, min_area: int = 0, output: str | None = None) -> dict:
    """Find contours in image using OpenCV, draw them on output image."""
    img, err = _load_image(path)
    if err:
        return err
    gray = img.convert("L")
    arr = np.array(gray)
    _, binary = cv2.threshold(arr, threshold, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if min_area > 0:
        contours = [c for c in contours if cv2.contourArea(c) >= min_area]
    # Draw on copy
    draw_img = img.convert("RGB")
    draw_arr = np.array(draw_img)
    cv2.drawContours(draw_arr, contours, -1, (0, 255, 0), 2)
    result_img = Image.fromarray(draw_arr)
    out = output or _output_path(path, "contours")
    result_img.save(out)
    return {"success": True, "output_path": out, "num_contours": len(contours)}
