"""Analysis tools: diff, histogram, edge detection, QR, background removal."""

import numpy as np
from PIL import Image

from mcp_raster._core import _load_image, _output_path


def raster_diff(path1: str, path2: str, output: str | None = None) -> dict:
    """Compute structural similarity (SSIM) between two images. Requires scikit-image."""
    try:
        from skimage.metrics import structural_similarity as ssim
    except ImportError:
        return {"success": False, "error": "EUNSUPPORTED",
                "detail": "Install: pip install mcp-images[analysis]"}
    img1, err = _load_image(path1)
    if err:
        return err
    img2, err2 = _load_image(path2)
    if err2:
        return err2
    size = (min(img1.width, img2.width), min(img1.height, img2.height))
    arr1 = np.array(img1.resize(size).convert("L"))
    arr2 = np.array(img2.resize(size).convert("L"))
    score = ssim(arr1, arr2, data_range=255)
    diff_arr = np.abs(arr1.astype(np.float32) - arr2.astype(np.float32)).astype(np.uint8)
    diff_img = Image.fromarray(diff_arr)
    out = output or _output_path(path1, "diff")
    diff_img.save(out)
    return {"success": True, "ssim": round(float(score), 4), "diff_image": out}


def raster_histogram(path: str, channel: str = "all") -> dict:
    """Return histogram values. channel: r, g, b, a, or all."""
    img, err = _load_image(path)
    if err:
        return err
    if channel == "all":
        result = {"success": True}
        ch_names = {"r": 0, "g": 1, "b": 2, "a": 3}
        bands = img.split()
        for name, idx in ch_names.items():
            if idx < len(bands):
                result[name] = bands[idx].histogram()
        return result
    ch_map = {"r": 0, "g": 1, "b": 2, "a": 3}
    idx = ch_map.get(channel.lower())
    if idx is None:
        return {"success": False, "error": "EUNSUPPORTED",
                "detail": f"Unknown channel: {channel}. Use r, g, b, a, or all"}
    bands = img.split()
    if idx >= len(bands):
        return {"success": False, "error": "EPROCESSING", "detail": f"Image has no channel '{channel}'"}
    return {"success": True, "histogram": bands[idx].histogram()}


def raster_edge(
    path: str,
    low_threshold: int = 50,
    high_threshold: int = 150,
    output: str | None = None,
) -> dict:
    """Canny edge detection."""
    import cv2
    img, err = _load_image(path)
    if err:
        return err
    gray = np.array(img.convert("L"))
    edges = cv2.Canny(gray, low_threshold, high_threshold)
    out_img = Image.fromarray(edges)
    out = output or _output_path(path, "edges")
    out_img.save(out)
    return {"success": True, "output_path": out}


def raster_qr(path: str) -> dict:
    """Decode QR codes and barcodes. Returns list of decoded texts. Requires pyzbar."""
    try:
        from pyzbar.pyzbar import decode
    except ImportError:
        return {"success": False, "error": "EUNSUPPORTED",
                "detail": "Install: pip install mcp-images[analysis]"}
    img, err = _load_image(path)
    if err:
        return err
    decoded = decode(img)
    codes = []
    for d in decoded:
        codes.append({
            "type": d.type,
            "data": d.data.decode("utf-8", errors="replace"),
        })
    return {"success": True, "codes": codes}


def raster_bgremove(path: str, output: str | None = None) -> dict:
    """Remove background from image. Returns RGBA image. Requires rembg."""
    try:
        from rembg import remove
    except ImportError:
        return {"success": False, "error": "EUNSUPPORTED",
                "detail": "Install: pip install mcp-images[analysis]"}
    img, err = _load_image(path)
    if err:
        return err
    result = remove(img)
    out = output or _output_path(path, "bgremoved")
    result.save(out)
    return {"success": True, "output_path": out}
