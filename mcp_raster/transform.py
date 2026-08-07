"""Transform tools: perspective, morphology, balance, padding, channels, compression."""

import os
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

from mcp_raster._core import _load_image, _output_path


def raster_perspective(
    path: str,
    src_points: list[list[int]],
    dst_points: list[list[int]],
    output: str | None = None,
) -> dict:
    """4-point perspective correction. src_points and dst_points are 4 [x,y] pairs."""
    img, err = _load_image(path)
    if err:
        return err
    src = np.array(src_points, dtype=np.float32)
    dst = np.array(dst_points, dtype=np.float32)
    if src.shape != (4, 2) or dst.shape != (4, 2):
        return {
            "success": False,
            "error": "EPROCESSING",
            "detail": "src_points and dst_points must each be 4 pairs of [x, y]",
        }
    matrix = cv2.getPerspectiveTransform(src, dst)
    arr = np.array(img.convert("RGB"))
    h, w = img.height, img.width
    result = cv2.warpPerspective(arr, matrix, (w, h))
    out_img = Image.fromarray(result)
    out = output or _output_path(path, "perspective")
    out_img.save(out)
    return {"success": True, "output_path": out}


_MORPH_OPS = {"dilate", "erode", "open", "close"}


def raster_morphology(
    path: str,
    operation: str = "dilate",
    kernel_size: int = 3,
    iterations: int = 1,
    output: str | None = None,
) -> dict:
    """Apply morphological operation: dilate, erode, open, close."""
    img, err = _load_image(path)
    if err:
        return err
    op = operation.lower()
    if op not in _MORPH_OPS:
        return {
            "success": False,
            "error": "EUNSUPPORTED",
            "detail": f"Unknown operation: {operation}. Available: {', '.join(sorted(_MORPH_OPS))}",
        }
    arr = np.array(img.convert("RGB"))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    if op == "dilate":
        morphed = cv2.dilate(arr, kernel, iterations=iterations)
    elif op == "erode":
        morphed = cv2.erode(arr, kernel, iterations=iterations)
    elif op == "open":
        morphed = cv2.morphologyEx(arr, cv2.MORPH_OPEN, kernel, iterations=iterations)
    else:  # close
        morphed = cv2.morphologyEx(arr, cv2.MORPH_CLOSE, kernel, iterations=iterations)
    out_img = Image.fromarray(morphed)
    out = output or _output_path(path, f"morph_{op}")
    out_img.save(out)
    return {"success": True, "output_path": out}


_BALANCE_MODES = {"equalize", "autocontrast", "auto_white"}


def raster_balance(path: str, mode: str = "autocontrast", output: str | None = None) -> dict:
    """Auto-balance image: equalize (histogram), autocontrast, auto_white."""
    img, err = _load_image(path)
    if err:
        return err
    m = mode.lower()
    if m not in _BALANCE_MODES:
        return {
            "success": False,
            "error": "EUNSUPPORTED",
            "detail": f"Unknown mode: {mode}. Available: {', '.join(sorted(_BALANCE_MODES))}",
        }
    if m == "equalize":
        gray = img.convert("L")
        gray = ImageOps.equalize(gray)
        img = gray.convert("RGB")
    elif m == "autocontrast":
        img = ImageOps.autocontrast(img)
    elif m == "auto_white":
        arr = np.array(img.convert("RGB"), dtype=np.float32)
        mean_b = arr[:, :, 0].mean()
        mean_g = arr[:, :, 1].mean()
        mean_r = arr[:, :, 2].mean()
        gray = (mean_b + mean_g + mean_r) / 3
        arr[:, :, 0] = np.clip(arr[:, :, 0] * (gray / max(mean_b, 1)), 0, 255)
        arr[:, :, 1] = np.clip(arr[:, :, 1] * (gray / max(mean_g, 1)), 0, 255)
        arr[:, :, 2] = np.clip(arr[:, :, 2] * (gray / max(mean_r, 1)), 0, 255)
        img = Image.fromarray(arr.astype(np.uint8))
    out = output or _output_path(path, f"balance_{m}")
    img.save(out)
    return {"success": True, "output_path": out}


def raster_padding(
    path: str,
    top: int = 0,
    right: int = 0,
    bottom: int = 0,
    left: int = 0,
    fill_color: str = "white",
    output: str | None = None,
) -> dict:
    """Add padding/border to image edges."""
    img, err = _load_image(path)
    if err:
        return err
    padded = ImageOps.expand(img, border=(left, top, right, bottom), fill=fill_color)
    out = output or _output_path(path, "padded")
    padded.save(out)
    return {"success": True, "output_path": out, "width": padded.width, "height": padded.height}


_CHANNEL_OPS = {"extract", "swap", "reorder"}


def raster_channels(
    path: str,
    operation: str = "extract",
    channels: list[int] | None = None,
    output: str | None = None,
) -> dict:
    """Channel operations: extract (single channel), swap, reorder.
    channels: list of channel indices (0=R, 1=G, 2=B, 3=A if RGBA).
    """
    img, err = _load_image(path)
    if err:
        return err
    op = operation.lower()
    if op not in _CHANNEL_OPS:
        return {
            "success": False,
            "error": "EUNSUPPORTED",
            "detail": f"Unknown operation: {operation}. Available: {', '.join(sorted(_CHANNEL_OPS))}",
        }
    bands = list(img.split())
    if channels is None:
        channels = list(range(len(bands)))

    if op == "extract":
        if not channels:
            selected = bands[0]
        else:
            selected = bands[channels[0]]
        out_img = selected.convert("L") if selected.mode != "L" else selected
    elif op == "swap" and len(channels) >= 2:
        idx1, idx2 = channels[0], channels[1]
        bands[idx1], bands[idx2] = bands[idx2], bands[idx1]
        out_img = Image.merge(img.mode, bands[: len(img.mode)])
    elif op == "reorder":
        reordered = [bands[i] for i in channels if i < len(bands)]
        mode_map = {1: "L", 3: "RGB", 4: "RGBA"}
        out_img = Image.merge(mode_map.get(len(reordered), "RGB"), reordered)
    else:
        out_img = img

    out = output or _output_path(path, f"channels_{op}")
    out_img.save(out)
    return {"success": True, "output_path": out}


def raster_compress(
    path: str,
    quality: int = 85,
    strip_metadata: bool = True,
    output: str | None = None,
) -> dict:
    """Compress image: reduce quality, strip EXIF metadata."""
    img, err = _load_image(path)
    if err:
        return err
    out = output or _output_path(path, "compressed")
    # Always output as .jpg for compression
    out = str(Path(out).with_suffix(".jpg"))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.save(out, format="JPEG", quality=quality, optimize=True)
    return {"success": True, "output_path": out, "size": os.path.getsize(out)}
