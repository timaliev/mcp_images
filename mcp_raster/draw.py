"""Draw tools for raster MCP: text overlay, shape drawing."""

from PIL import ImageDraw, ImageFont

from mcp_raster._core import _load_image, _output_path


def raster_text(
    path: str,
    text: str,
    x: int = 0,
    y: int = 0,
    size: int = 20,
    color: str = "black",
    output: str | None = None,
) -> dict:
    """Overlay text on image at (x,y) with given size and color."""
    img, err = _load_image(path)
    if err:
        return err
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
    except (OSError, IOError):
        font = ImageFont.load_default()
    draw.text((x, y), text, fill=color, font=font)
    out = output or _output_path(path, "text")
    img.save(out)
    return {"success": True, "output_path": out}


def raster_draw(
    path: str,
    shape: str,
    coords: list[int],
    color: str = "red",
    width: int = 2,
    output: str | None = None,
) -> dict:
    """Draw shape on image. Supported: rect, circle, line, arrow.
    rect coords: [x1, y1, x2, y2]
    circle coords: [cx, cy, radius]
    line/arrow coords: [x1, y1, x2, y2]
    """
    img, err = _load_image(path)
    if err:
        return err
    draw = ImageDraw.Draw(img)
    shape_lower = shape.lower()

    if shape_lower == "rect":
        draw.rectangle(coords, outline=color, width=width)
    elif shape_lower == "circle":
        cx, cy, r = coords
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=width)
    elif shape_lower == "line":
        draw.line(coords, fill=color, width=width)
    elif shape_lower == "arrow":
        import math
        x1, y1, x2, y2 = coords
        draw.line([x1, y1, x2, y2], fill=color, width=width)
        angle = math.atan2(y2 - y1, x2 - x1)
        arrow_len = max(10, width * 3)
        ax = x2 - arrow_len * math.cos(angle - 0.45)
        ay = y2 - arrow_len * math.sin(angle - 0.45)
        bx = x2 - arrow_len * math.cos(angle + 0.45)
        by = y2 - arrow_len * math.sin(angle + 0.45)
        draw.polygon([x2, y2, ax, ay, bx, by], fill=color)
    else:
        return {"success": False, "error": "EUNSUPPORTED",
                "detail": f"Unknown shape: {shape}. Available: rect, circle, line, arrow"}

    out = output or _output_path(path, shape_lower)
    img.save(out)
    return {"success": True, "output_path": out}
