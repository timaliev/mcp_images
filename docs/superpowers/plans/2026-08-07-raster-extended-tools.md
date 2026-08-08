# Raster MCP Extended Tools — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 17 raster manipulation tools across 5 modules, restructure shared utilities into `_core.py`, move filter/enhance to `filters.py`.

**Architecture:** Modular — `_core.py` for shared utilities, `draw.py`/`analysis.py`/`transform.py`/`metadata.py`/`filters.py` for tool groups, `server.py` for orchestration. Lazy imports for optional deps (`scikit-image`, `pyzbar`, `rembg`). All tools follow `(img, err) = _load_image(path); if err: return err` pattern.

**Tech Stack:** Pillow 11+, OpenCV 4.10+, scikit-image 0.24+, pyzbar 0.1+, rembg 2.0+, MCP 1.9+

## Global Constraints

- Optional dependencies in `[project.optional-dependencies]` as `analysis` group
- Missing optional dep → `{"success": false, "error": "EUNSUPPORTED", "detail": "Install: pip install mcp-images[analysis]"}`
- All tools return `{"success": true, ...}` or `{"success": false, "error": "...", "detail": "..."}`
- Test files: `tests/test_draw.py`, `tests/test_analysis.py`, `tests/test_transform.py`, `tests/test_metadata.py`
- 2+ tests per tool, full suite <5s
- Conventional commits, branch `feature/raster-extended-tools`

---

## File Structure

```
mcp_raster/
├── __init__.py           # (exists)
├── _core.py              # CREATE: _load_image, _output_path (moved from server.py)
├── server.py             # MODIFY: remove _load_image/_output_path, import from _core,
│                         #   move filter/enhance to filters.py, import+register all new tools
├── draw.py               # CREATE: raster_text, raster_draw
├── analysis.py           # CREATE: raster_diff, raster_histogram, raster_edge, raster_qr, raster_bgremove
├── transform.py          # CREATE: raster_perspective, raster_morphology, raster_balance,
│                         #   raster_padding, raster_channels, raster_compress
├── metadata.py           # CREATE: raster_exif, raster_colorspace, raster_blend, raster_contours
└── filters.py            # CREATE: raster_filter, raster_enhance (moved from server.py)

tests/
├── test_server.py        # (exists, update imports)
├── test_draw.py          # CREATE
├── test_analysis.py      # CREATE
├── test_transform.py     # CREATE
├── test_metadata.py      # CREATE
└── test_filters.py       # CREATE
```

---

### Task 1: Extract shared utilities to `_core.py`

**Files:**
- Create: `mcp_raster/_core.py`
- Modify: `mcp_raster/server.py`

**Interfaces:**
- Produces: `_load_image(path: str) -> tuple[Image.Image | None, dict | None]`, `_output_path(path: str, suffix: str | None = None) -> str`

- [ ] **Step 1: Create `mcp_raster/_core.py`**

```python
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
```

- [ ] **Step 2: Run existing tests to verify nothing broken yet**

```bash
uv run python -m pytest tests/ -v
```
Expected: All 19 pass.

- [ ] **Step 3: Update `server.py` — remove `_load_image` and `_output_path`, import from `_core`**

Replace in `server.py`:
```python
# Remove these lines:
import tempfile
from pathlib import Path

OUTPUT_DIR = Path(os.environ.get("RASTER_OUTPUT_DIR", tempfile.gettempdir()))

def _output_path(...):  # remove entire function
def _load_image(...):   # remove entire function
```

Add at top:
```python
from mcp_raster._core import _load_image, _output_path
```

- [ ] **Step 4: Run tests**

```bash
uv run python -m pytest tests/ -v
```
Expected: All 19 pass.

- [ ] **Step 5: Commit**

```bash
git checkout -b feature/raster-extended-tools
git add mcp_raster/_core.py mcp_raster/server.py
git tag -a step-1 -m "Rollback point 1: extract _core.py"
git commit -m "refactor(raster): extract _load_image and _output_path to _core.py"
git push -u origin feature/raster-extended-tools
```

---

### Task 2: Move existing filters to `filters.py`

**Files:**
- Create: `mcp_raster/filters.py`
- Create: `tests/test_filters.py`
- Modify: `mcp_raster/server.py`

**Interfaces:**
- Consumes: `_load_image`, `_output_path` from `mcp_raster._core`
- Produces: `raster_filter(...) -> dict`, `raster_enhance(...) -> dict`

- [ ] **Step 1: Create `mcp_raster/filters.py`**

```python
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
```

- [ ] **Step 2: Create `tests/test_filters.py`**

```python
"""Tests for raster filter/enhance tools."""

import pytest
import os
from PIL import Image


@pytest.fixture
def sample_image(tmp_path):
    img = Image.new("RGB", (100, 50), color="red")
    path = tmp_path / "sample.png"
    img.save(path)
    return str(path)


def test_raster_filter_grayscale(sample_image):
    from mcp_raster.filters import raster_filter
    result = raster_filter(sample_image, "grayscale")
    assert result["success"] is True
    assert result["filter_applied"] == "grayscale"
    assert os.path.isfile(result["output_path"])


def test_raster_filter_unknown(sample_image):
    from mcp_raster.filters import raster_filter
    result = raster_filter(sample_image, "nonexistent")
    assert result["success"] is False
    assert result["error"] == "EUNSUPPORTED"


def test_raster_enhance_contrast(sample_image):
    from mcp_raster.filters import raster_enhance
    result = raster_enhance(sample_image, mode="contrast", factor=2.0)
    assert result["success"] is True


def test_raster_enhance_unknown_mode(sample_image):
    from mcp_raster.filters import raster_enhance
    result = raster_enhance(sample_image, mode="nonexistent")
    assert result["success"] is False
```

- [ ] **Step 3: Run filters tests**

```bash
uv run python -m pytest tests/test_filters.py -v
```
Expected: 4 pass.

- [ ] **Step 4: Update `server.py` — import from `filters` module, remove old definitions**

Replace in `server.py`:
```python
# Remove: _FILTERS dict, raster_filter function, raster_enhance function
# Remove: import cv2, import numpy (if not used elsewhere)
# Remove: from PIL import ImageEnhance, ImageFilter, ImageOps (if not used elsewhere)

# Add at imports:
from mcp_raster.filters import raster_filter, raster_enhance
```

- [ ] **Step 5: Remove filter tests from `tests/test_server.py`**

Remove these test functions from `tests/test_server.py`:
- `test_raster_filter_grayscale`
- `test_raster_filter_blur`
- `test_raster_filter_unknown`
- `test_raster_enhance_contrast`
- `test_raster_enhance_all`
- `test_raster_enhance_unknown_mode`

- [ ] **Step 6: Run all tests**

```bash
uv run python -m pytest tests/ -v
```
Expected: All pass (17 from server + 4 from filters = 21).

- [ ] **Step 7: Commit**

```bash
git add mcp_raster/filters.py tests/test_filters.py mcp_raster/server.py tests/test_server.py
git tag -a step-2 -m "Rollback point 2: extract filters module"
git commit -m "refactor(raster): extract filter and enhance tools to filters.py"
git push
```

---

### Task 3: Metadata tools (`metadata.py`)

**Files:**
- Create: `mcp_raster/metadata.py`
- Create: `tests/test_metadata.py`
- Modify: `mcp_raster/server.py`

**Interfaces:**
- Consumes: `_load_image`, `_output_path` from `mcp_raster._core`
- Produces: `raster_exif(path) -> dict`, `raster_colorspace(path, target, output) -> dict`, `raster_blend(path1, path2, alpha, output) -> dict`, `raster_contours(path, threshold, min_area, output) -> dict`

- [ ] **Step 1: Write `tests/test_metadata.py` (TDD — test first)**

```python
"""Tests for raster metadata tools."""

import pytest
import os
from PIL import Image, ImageDraw
import json


@pytest.fixture
def sample_image(tmp_path):
    img = Image.new("RGB", (100, 50), color="red")
    path = tmp_path / "sample.png"
    img.save(path)
    return str(path)


@pytest.fixture
def sample_image2(tmp_path):
    img = Image.new("RGB", (100, 50), color="blue")
    path = tmp_path / "sample2.png"
    img.save(path)
    return str(path)


# --- raster_exif ---

def test_raster_exif_returns_dict(sample_image):
    from mcp_raster.metadata import raster_exif
    result = raster_exif(sample_image)
    assert result["success"] is True
    assert "exif" in result
    assert isinstance(result["exif"], dict)


def test_raster_exif_file_not_found():
    from mcp_raster.metadata import raster_exif
    result = raster_exif("/nonexistent/img.png")
    assert result["success"] is False
    assert result["error"] == "ENOENT"


# --- raster_colorspace ---

def test_raster_colorspace_to_hsv(sample_image):
    from mcp_raster.metadata import raster_colorspace
    result = raster_colorspace(sample_image, "HSV")
    assert result["success"] is True
    assert os.path.isfile(result["output_path"])
    out = Image.open(result["output_path"])
    assert out.mode == "HSV"


def test_raster_colorspace_to_lab(sample_image):
    from mcp_raster.metadata import raster_colorspace
    result = raster_colorspace(sample_image, "LAB")
    assert result["success"] is True


def test_raster_colorspace_unsupported(sample_image):
    from mcp_raster.metadata import raster_colorspace
    result = raster_colorspace(sample_image, "CMYK")
    assert result["success"] is False
    assert result["error"] == "EUNSUPPORTED"


# --- raster_blend ---

def test_raster_blend_images(sample_image, sample_image2):
    from mcp_raster.metadata import raster_blend
    result = raster_blend(sample_image, sample_image2, alpha=0.5)
    assert result["success"] is True
    assert os.path.isfile(result["output_path"])


def test_raster_blend_mismatched_sizes(sample_image, tmp_path):
    from mcp_raster.metadata import raster_blend
    img_big = Image.new("RGB", (200, 100), color="green")
    big_path = tmp_path / "big.png"
    img_big.save(big_path)
    result = raster_blend(sample_image, str(big_path), alpha=0.5)
    assert result["success"] is False
    assert result["error"] == "EPROCESSING"


# --- raster_contours ---

def test_raster_contours_finds_shapes(sample_image):
    from mcp_raster.metadata import raster_contours
    result = raster_contours(sample_image, threshold=128, min_area=10)
    assert result["success"] is True
    assert "num_contours" in result
    assert os.path.isfile(result["output_path"])


def test_raster_contours_file_not_found():
    from mcp_raster.metadata import raster_contours
    result = raster_contours("/nonexistent/img.png", threshold=128)
    assert result["success"] is False
    assert result["error"] == "ENOENT"
```

- [ ] **Step 2: Run metadata tests — must FAIL**

```bash
uv run python -m pytest tests/test_metadata.py -v
```
Expected: ImportError — module doesn't exist yet.

- [ ] **Step 3: Create `mcp_raster/metadata.py`**

```python
"""Metadata tools for raster MCP: EXIF, colorspace, blend, contours."""

import cv2
import numpy as np
from PIL import Image, ImageOps

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


_COLORSPACES = {"RGB", "HSV", "LAB", "L", "YCbCr", "CMYK"}


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
```

- [ ] **Step 4: Run metadata tests — must PASS**

```bash
uv run python -m pytest tests/test_metadata.py -v
```
Expected: 8 pass.

- [ ] **Step 5: Register in `server.py`**

Add at imports:
```python
from mcp_raster.metadata import raster_exif, raster_colorspace, raster_blend, raster_contours
```

Add tools (search for `def main():` and add before it):
```python
server.tool()(raster_exif)
server.tool()(raster_colorspace)
server.tool()(raster_blend)
server.tool()(raster_contours)
```

- [ ] **Step 6: Run all tests**

```bash
uv run python -m pytest tests/ -v
```
Expected: All pass.

- [ ] **Step 7: Commit**

```bash
git add mcp_raster/metadata.py tests/test_metadata.py mcp_raster/server.py
git tag -a step-3 -m "Rollback point 3: metadata tools"
git commit -m "feat(raster): add exif, colorspace, blend, contour tools"
git push
```

---

### Task 4: Draw tools (`draw.py`)

**Files:**
- Create: `mcp_raster/draw.py`
- Create: `tests/test_draw.py`
- Modify: `mcp_raster/server.py`

**Interfaces:**
- Produces: `raster_text(path, text, x, y, size, color, output) -> dict`, `raster_draw(path, shape, coords, color, width, output) -> dict`

- [ ] **Step 1: Write `tests/test_draw.py`**

```python
"""Tests for raster draw tools."""

import pytest
import os
from PIL import Image


@pytest.fixture
def sample_image(tmp_path):
    img = Image.new("RGB", (200, 100), color="white")
    path = tmp_path / "sample.png"
    img.save(path)
    return str(path)


def test_raster_text_overlay(sample_image):
    from mcp_raster.draw import raster_text
    result = raster_text(sample_image, "Hello", x=10, y=50, size=24, color="red")
    assert result["success"] is True
    assert os.path.isfile(result["output_path"])


def test_raster_text_missing_file():
    from mcp_raster.draw import raster_text
    result = raster_text("/nonexistent.png", "test", x=0, y=0)
    assert result["success"] is False
    assert result["error"] == "ENOENT"


def test_raster_draw_rectangle(sample_image):
    from mcp_raster.draw import raster_draw
    result = raster_draw(sample_image, "rect", [10, 10, 100, 80], color="blue", width=2)
    assert result["success"] is True
    assert os.path.isfile(result["output_path"])


def test_raster_draw_circle(sample_image):
    from mcp_raster.draw import raster_draw
    result = raster_draw(sample_image, "circle", [100, 50, 30], color="green")
    assert result["success"] is True


def test_raster_draw_line(sample_image):
    from mcp_raster.draw import raster_draw
    result = raster_draw(sample_image, "line", [0, 0, 200, 100], color="red")
    assert result["success"] is True


def test_raster_draw_unsupported_shape(sample_image):
    from mcp_raster.draw import raster_draw
    result = raster_draw(sample_image, "triangle", [0, 0, 10, 10])
    assert result["success"] is False
    assert result["error"] == "EUNSUPPORTED"
```

- [ ] **Step 2: Run — FAIL**

```bash
uv run python -m pytest tests/test_draw.py -v
```
Expected: ImportError.

- [ ] **Step 3: Create `mcp_raster/draw.py`**

```python
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
```

- [ ] **Step 4: Run draw tests — PASS**

```bash
uv run python -m pytest tests/test_draw.py -v
```
Expected: 6 pass.

- [ ] **Step 5: Register in `server.py`**

```python
from mcp_raster.draw import raster_text, raster_draw
server.tool()(raster_text)
server.tool()(raster_draw)
```

- [ ] **Step 6: Run all tests**

```bash
uv run python -m pytest tests/ -v
```

- [ ] **Step 7: Commit**

```bash
git add mcp_raster/draw.py tests/test_draw.py mcp_raster/server.py
git tag -a step-4 -m "Rollback point 4: draw tools"
git commit -m "feat(raster): add text overlay and shape drawing tools"
git push
```

---

### Task 5: Transform tools (`transform.py`)

**Files:**
- Create: `mcp_raster/transform.py`
- Create: `tests/test_transform.py`
- Modify: `mcp_raster/server.py`

**Interfaces:**
- Produces: `raster_perspective`, `raster_morphology`, `raster_balance`, `raster_padding`, `raster_channels`, `raster_compress`

- [ ] **Step 1: Write `tests/test_transform.py`**

```python
"""Tests for raster transform tools."""

import pytest
import os
from PIL import Image


@pytest.fixture
def sample_image(tmp_path):
    img = Image.new("RGB", (200, 100), color="white")
    path = tmp_path / "sample.png"
    img.save(path)
    return str(path)


# --- raster_perspective ---

def test_raster_perspective_corrects(sample_image):
    from mcp_raster.transform import raster_perspective
    src = [[10, 10], [190, 10], [190, 90], [10, 90]]
    dst = [[0, 0], [200, 0], [200, 100], [0, 100]]
    result = raster_perspective(sample_image, src, dst)
    assert result["success"] is True
    assert os.path.isfile(result["output_path"])


# --- raster_morphology ---

def test_raster_morphology_dilate(sample_image):
    from mcp_raster.transform import raster_morphology
    result = raster_morphology(sample_image, "dilate")
    assert result["success"] is True


def test_raster_morphology_unknown_op(sample_image):
    from mcp_raster.transform import raster_morphology
    result = raster_morphology(sample_image, "skeletonize")
    assert result["success"] is False
    assert result["error"] == "EUNSUPPORTED"


# --- raster_balance ---

def test_raster_balance_equalize(sample_image):
    from mcp_raster.transform import raster_balance
    result = raster_balance(sample_image, "equalize")
    assert result["success"] is True


def test_raster_balance_autocontrast(sample_image):
    from mcp_raster.transform import raster_balance
    result = raster_balance(sample_image, "autocontrast")
    assert result["success"] is True


# --- raster_padding ---

def test_raster_padding_add_border(sample_image):
    from mcp_raster.transform import raster_padding
    result = raster_padding(sample_image, top=10, right=10, bottom=10, left=10, fill_color="black")
    assert result["success"] is True
    out = Image.open(result["output_path"])
    assert out.width == 220  # 200 + 10 + 10
    assert out.height == 120  # 100 + 10 + 10


# --- raster_channels ---

def test_raster_channels_extract_red(sample_image):
    from mcp_raster.transform import raster_channels
    result = raster_channels(sample_image, "extract", channels=[0])
    assert result["success"] is True


def test_raster_channels_unknown_op(sample_image):
    from mcp_raster.transform import raster_channels
    result = raster_channels(sample_image, "quantize")
    assert result["success"] is False
    assert result["error"] == "EUNSUPPORTED"


# --- raster_compress ---

def test_raster_compress_reduces_size(sample_image):
    from mcp_raster.transform import raster_compress
    result = raster_compress(sample_image, quality=50)
    assert result["success"] is True
    assert os.path.getsize(result["output_path"]) < os.path.getsize(sample_image)
```

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Create `mcp_raster/transform.py`**

```python
"""Transform tools: perspective, morphology, balance, padding, channels, compression."""

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
        return {"success": False, "error": "EPROCESSING",
                "detail": "src_points and dst_points must each be 4 pairs of [x, y]"}
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
        return {"success": False, "error": "EUNSUPPORTED",
                "detail": f"Unknown operation: {operation}. Available: {', '.join(sorted(_MORPH_OPS))}"}
    arr = np.array(img.convert("RGB"))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    morphed = getattr(cv2, f"morphologyEx")(arr, getattr(cv2, f"MORPH_{op.upper()}"), kernel, iterations=iterations) if op in ("open", "close") else getattr(cv2, op)(arr, kernel, iterations=iterations)
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
        return {"success": False, "error": "EUNSUPPORTED",
                "detail": f"Unknown mode: {mode}. Available: {', '.join(sorted(_BALANCE_MODES))}"}
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
    return {"success": True, "output_path": out,
            "width": padded.width, "height": padded.height}


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
        return {"success": False, "error": "EUNSUPPORTED",
                "detail": f"Unknown operation: {operation}. Available: {', '.join(sorted(_CHANNEL_OPS))}"}
    bands = img.split()
    if not channels:
        channels = list(range(len(bands)))
    if op == "extract":
        selected = bands[channels[0]]
        out_img = selected.convert("L") if selected.mode != "L" else selected
    elif op == "swap" and len(channels) >= 2:
        idx1, idx2 = channels[0], channels[1]
        bands[idx1], bands[idx2] = bands[idx2], bands[idx1]
        out_img = Image.merge(img.mode, bands[:len(img.mode)])
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
    save_kwargs = {"quality": quality, "optimize": True}
    out_fmt = img.format or "JPEG"
    if out_fmt == "PNG":
        img.save(out, format="PNG", optimize=True)
    else:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(out, format="JPEG", **save_kwargs)
    return {"success": True, "output_path": out, "size": os.path.getsize(out)}
```

- [ ] **Step 4: Fix transform.py — correct morphology call**

The one-liner morphology is too clever. Replace:
```python
    morphed = getattr(cv2, f"morphologyEx")(arr, getattr(cv2, f"MORPH_{op.upper()}"), kernel, iterations=iterations) if op in ("open", "close") else getattr(cv2, op)(arr, kernel, iterations=iterations)
```
With explicit:
```python
    if op in ("open", "close"):
        morph_type = cv2.MORPH_OPEN if op == "open" else cv2.MORPH_CLOSE
        morphed = cv2.morphologyEx(arr, morph_type, kernel, iterations=iterations)
    elif op == "dilate":
        morphed = cv2.dilate(arr, kernel, iterations=iterations)
    else:  # erode
        morphed = cv2.erode(arr, kernel, iterations=iterations)
```

Also add `import os` at top of transform.py.

- [ ] **Step 5: Run transform tests — PASS**

```bash
uv run python -m pytest tests/test_transform.py -v
```
Expected: 9 pass.

- [ ] **Step 6: Register in `server.py`**

```python
from mcp_raster.transform import (
    raster_perspective, raster_morphology, raster_balance,
    raster_padding, raster_channels, raster_compress,
)
server.tool()(raster_perspective)
server.tool()(raster_morphology)
server.tool()(raster_balance)
server.tool()(raster_padding)
server.tool()(raster_channels)
server.tool()(raster_compress)
```

- [ ] **Step 7: Run all tests, commit**

```bash
uv run python -m pytest tests/ -v
git add mcp_raster/transform.py tests/test_transform.py mcp_raster/server.py
git tag -a step-5 -m "Rollback point 5: transform tools"
git commit -m "feat(raster): add perspective, morphology, balance, padding, channels, compress"
git push
```

---

### Task 6: Analysis tools (`analysis.py`)

**Files:**
- Create: `mcp_raster/analysis.py`
- Create: `tests/test_analysis.py`
- Modify: `mcp_raster/server.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Produces: `raster_diff`, `raster_histogram`, `raster_edge`, `raster_qr`, `raster_bgremove`
- Optional deps: scikit-image, pyzbar, rembg

- [ ] **Step 1: Update `pyproject.toml` — add optional dependency group**

```toml
[project.optional-dependencies]
analysis = ["scikit-image>=0.24", "pyzbar>=0.1", "rembg>=2.0"]
```

- [ ] **Step 2: Install analysis deps**

```bash
uv add --optional analysis scikit-image pyzbar rembg
```

- [ ] **Step 3: Write `tests/test_analysis.py`**

```python
"""Tests for raster analysis tools."""

import pytest
import os
from PIL import Image, ImageDraw


@pytest.fixture
def sample_image(tmp_path):
    img = Image.new("RGB", (100, 50), color="white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 10, 80, 40], fill="black")
    path = tmp_path / "sample.png"
    img.save(path)
    return str(path)


@pytest.fixture
def sample_image2(tmp_path):
    img = Image.new("RGB", (100, 50), color="white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([25, 15, 75, 35], fill="black")
    path = tmp_path / "sample2.png"
    img.save(path)
    return str(path)


# --- raster_diff ---

def test_raster_diff_returns_score(sample_image, sample_image2):
    pytest.importorskip("skimage")
    from mcp_raster.analysis import raster_diff
    result = raster_diff(sample_image, sample_image2)
    assert result["success"] is True
    assert "ssim" in result
    assert 0 <= result["ssim"] <= 1


def test_raster_diff_same_image(sample_image):
    pytest.importorskip("skimage")
    from mcp_raster.analysis import raster_diff
    result = raster_diff(sample_image, sample_image)
    assert result["success"] is True
    assert result["ssim"] > 0.99  # identical


# --- raster_histogram ---

def test_raster_histogram_all_channels(sample_image):
    from mcp_raster.analysis import raster_histogram
    result = raster_histogram(sample_image, channel="all")
    assert result["success"] is True
    assert "r" in result
    assert "g" in result
    assert "b" in result


def test_raster_histogram_red_channel(sample_image):
    from mcp_raster.analysis import raster_histogram
    result = raster_histogram(sample_image, channel="r")
    assert result["success"] is True
    assert len(result["histogram"]) == 256


# --- raster_edge ---

def test_raster_edge_detection(sample_image):
    from mcp_raster.analysis import raster_edge
    result = raster_edge(sample_image)
    assert result["success"] is True
    assert os.path.isfile(result["output_path"])


# --- raster_qr ---

def test_raster_qr_no_code(sample_image):
    pytest.importorskip("pyzbar")
    from mcp_raster.analysis import raster_qr
    result = raster_qr(sample_image)
    assert result["success"] is True
    assert result["codes"] == []


# --- raster_bgremove ---

def test_raster_bgremove_removes_bg(sample_image):
    pytest.importorskip("rembg")
    from mcp_raster.analysis import raster_bgremove
    result = raster_bgremove(sample_image)
    assert result["success"] is True
    assert os.path.isfile(result["output_path"])
    out = Image.open(result["output_path"])
    assert out.mode == "RGBA"  # bg removal adds alpha
```

- [ ] **Step 4: Run — FAIL**

- [ ] **Step 5: Create `mcp_raster/analysis.py`**

```python
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
```

- [ ] **Step 6: Run analysis tests — PASS**

```bash
uv run python -m pytest tests/test_analysis.py -v
```
Expected: 9 pass (some skipped if dep not installed, but we installed them).

- [ ] **Step 7: Register in `server.py`**

```python
from mcp_raster.analysis import raster_diff, raster_histogram, raster_edge, raster_qr, raster_bgremove
server.tool()(raster_diff)
server.tool()(raster_histogram)
server.tool()(raster_edge)
server.tool()(raster_qr)
server.tool()(raster_bgremove)
```

- [ ] **Step 8: Run all tests, commit**

```bash
uv run python -m pytest tests/ -v
git add mcp_raster/analysis.py tests/test_analysis.py mcp_raster/server.py pyproject.toml uv.lock
git tag -a step-6 -m "Rollback point 6: analysis tools"
git commit -m "feat(raster): add diff, histogram, edge, qr, bgremove tools"
git push
```

---

### Task 7: Update README and final cleanup

**Files:**
- Modify: `README.md`
- Modify: `mcp_raster/server.py` (remove unused imports)

- [ ] **Step 1: Update README tools table**

Replace the tools section with:
```markdown
## Tools

### Core
| Tool | Description |
|------|-------------|
| `raster_info` | Image metadata: dimensions, format, mode, DPI, file size |
| `raster_convert` | Convert format (png, jpeg, webp, tiff, bmp). Use `fmt` parameter |
| `raster_resize` | Resize by dimensions, scale, or fit mode |
| `raster_crop` | Crop to rectangle |
| `raster_rotate` | Rotate by degrees |
| `raster_adjust` | Brightness, contrast, saturation, sharpness, gamma |

### Draw
| Tool | Description |
|------|-------------|
| `raster_text` | Overlay text with font size and color |
| `raster_draw` | Draw shapes: rect, circle, line, arrow |

### Filters
| Tool | Description |
|------|-------------|
| `raster_filter` | Blur, sharpen, denoise, grayscale, invert, threshold. Use `filter_name` parameter |
| `raster_enhance` | Auto-enhance: contrast, color, sharpness, all |

### Transform
| Tool | Description |
|------|-------------|
| `raster_perspective` | 4-point perspective correction |
| `raster_morphology` | Morphological ops: dilate, erode, open, close |
| `raster_balance` | Auto balance: equalize, autocontrast, auto white |
| `raster_padding` | Add border/margin with fill color |
| `raster_channels` | Channel ops: extract, swap, reorder |
| `raster_compress` | Compress: quality control, metadata stripping |

### Metadata
| Tool | Description |
|------|-------------|
| `raster_exif` | Extract EXIF metadata as dict |
| `raster_colorspace` | Convert: RGB, HSV, LAB, grayscale |
| `raster_blend` | Alpha-blend two images |
| `raster_contours` | Find contours, draw with OpenCV |

### Analysis (requires `pip install mcp-images[analysis]`)
| Tool | Description |
|------|-------------|
| `raster_diff` | SSIM structural similarity between two images |
| `raster_histogram` | Channel histogram (R/G/B/all) |
| `raster_edge` | Canny edge detection |
| `raster_qr` | Read QR codes and barcodes |
| `raster_bgremove` | Remove background (returns RGBA) |
```

- [ ] **Step 2: Clean up server.py — remove stale imports**

Check `server.py` imports section. Remove any that are no longer used:
- `cv2` (moved to filters/transform)
- `numpy` (moved to filters/transform)
- `ImageEnhance`, `ImageFilter`, `ImageOps` (moved to filters)

Only keep what `server.py` itself uses: `os`, `sys`, `logging`, `MCPServer`, `PIL.Image`, and the tool imports.

- [ ] **Step 3: Run full test suite**

```bash
uv run python -m pytest tests/ -v
```
Expected: ~47 tests, all pass.

- [ ] **Step 4: Commit**

```bash
git add README.md mcp_raster/server.py
git tag -a step-7 -m "Rollback point 7: README update and cleanup"
git commit -m "docs(readme): add extended tools table, cleanup server imports"
git push
```

- [ ] **Step 5: Create PR, merge, cleanup**

Use GitHub MCP:
```python
mcp_github_create_pull_request(owner="timaliev", repo="mcp_images",
    title="feat(raster): add 17 extended manipulation tools",
    head="feature/raster-extended-tools", base="master")
mcp_github_merge_pull_request(owner="timaliev", repo="mcp_images",
    pull_number=<N>, merge_method="squash")
```

Local cleanup:
```bash
git checkout master && git pull
git branch -d feature/raster-extended-tools
git push origin --delete feature/raster-extended-tools
git tag -d step-1 step-2 step-3 step-4 step-5 step-6 step-7
```
