"""Integration tests — all tools registered and smoke-test each."""

import pytest
import os
from pathlib import Path
from PIL import Image

from mcp_raster.server import server

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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

@pytest.fixture
def sample_rgba(tmp_path):
    img = Image.new("RGBA", (100, 50), color=(255, 0, 0, 128))
    path = tmp_path / "rgba.png"
    img.save(path)
    return str(path)

@pytest.fixture
def sample_jpeg(tmp_path):
    img = Image.new("RGB", (100, 50), color="green")
    path = tmp_path / "sample.jpg"
    img.save(path, "JPEG")
    return str(path)

# ---------------------------------------------------------------------------
# Test: all tools registered
# ---------------------------------------------------------------------------

EXPECTED_TOOLS = {
    # Core (backend-decorated)
    "raster_info", "raster_convert", "raster_resize", "raster_crop",
    "raster_rotate", "raster_adjust",
    # Draw
    "raster_text", "raster_draw",
    # Filters
    "raster_filter", "raster_enhance",
    # Transform
    "raster_perspective", "raster_morphology", "raster_balance",
    "raster_padding", "raster_channels", "raster_compress",
    # Analysis
    "raster_diff", "raster_histogram", "raster_edge", "raster_qr",
    "raster_bgremove",
    # Metadata
    "raster_exif", "raster_colorspace", "raster_blend", "raster_contours",
}

def test_all_tools_registered():
    """Every tool in EXPECTED_TOOLS must be registered. Count must match."""
    registered = {t.name for t in server._tool_manager.list_tools()}
    assert registered == EXPECTED_TOOLS, (
        f"Missing: {EXPECTED_TOOLS - registered}\n"
        f"Extra: {registered - EXPECTED_TOOLS}"
    )
    assert len(registered) == 25, f"Expected 25 tools, got {len(registered)}"


# ---------------------------------------------------------------------------
# Smoke tests — each tool called once
# ---------------------------------------------------------------------------

def test_smoke_info(sample_image):
    from mcp_raster.server import raster_info
    result = raster_info(sample_image)
    assert result["success"] is True
    assert result["width"] == 100
    assert result["height"] == 50
    assert result["format"] == "PNG"

def test_smoke_convert(sample_image):
    from mcp_raster.server import raster_convert
    result = raster_convert(sample_image, "jpeg")
    assert result["success"] is True
    assert result["format"] == "jpeg"

def test_smoke_resize(sample_image):
    from mcp_raster.server import raster_resize
    result = raster_resize(sample_image, width=50, height=25)
    assert result["success"] is True
    assert result["width"] == 50
    assert result["height"] == 25

def test_smoke_crop(sample_image):
    from mcp_raster.server import raster_crop
    result = raster_crop(sample_image, left=10, top=10, right=50, bottom=40)
    assert result["success"] is True

def test_smoke_rotate(sample_image):
    from mcp_raster.server import raster_rotate
    result = raster_rotate(sample_image, degrees=90)
    assert result["success"] is True

def test_smoke_adjust(sample_image):
    from mcp_raster.server import raster_adjust
    result = raster_adjust(sample_image, brightness=1.1)
    assert result["success"] is True

def test_smoke_text(sample_image):
    from mcp_raster.server import raster_text
    result = raster_text(sample_image, text="TEST", x=10, y=10, size=12, color="white")
    assert result["success"] is True

def test_smoke_draw_rect(sample_image):
    from mcp_raster.server import raster_draw
    result = raster_draw(sample_image, shape="rect", coords=[5, 5, 50, 40], color="blue")
    assert result["success"] is True

def test_smoke_draw_circle(sample_image):
    from mcp_raster.server import raster_draw
    result = raster_draw(sample_image, shape="circle", coords=[50, 25, 20], color="green")
    assert result["success"] is True

def test_smoke_draw_line(sample_image):
    from mcp_raster.server import raster_draw
    result = raster_draw(sample_image, shape="line", coords=[0, 0, 50, 25], color="red")
    assert result["success"] is True

def test_smoke_filter(sample_image):
    from mcp_raster.server import raster_filter
    result = raster_filter(sample_image, "grayscale")
    assert result["success"] is True

def test_smoke_enhance(sample_image):
    from mcp_raster.server import raster_enhance
    result = raster_enhance(sample_image, mode="contrast", factor=1.5)
    assert result["success"] is True

def test_smoke_perspective(sample_image):
    from mcp_raster.server import raster_perspective
    result = raster_perspective(
        sample_image,
        src_points=[[0, 0], [99, 0], [99, 49], [0, 49]],
        dst_points=[[5, 5], [94, 0], [99, 44], [0, 49]],
    )
    assert result["success"] is True

def test_smoke_morphology(sample_image):
    from mcp_raster.server import raster_morphology
    result = raster_morphology(sample_image, "dilate", kernel_size=3)
    assert result["success"] is True

def test_smoke_balance(sample_image):
    from mcp_raster.server import raster_balance
    result = raster_balance(sample_image, mode="equalize")
    assert result["success"] is True

def test_smoke_padding(sample_image):
    from mcp_raster.server import raster_padding
    result = raster_padding(sample_image, top=5, right=5, bottom=5, left=5, fill_color="white")
    assert result["success"] is True

def test_smoke_channels(sample_image):
    from mcp_raster.server import raster_channels
    result = raster_channels(sample_image, operation="extract", channels=[0])
    assert result["success"] is True

def test_smoke_compress(sample_image):
    from mcp_raster.server import raster_compress
    result = raster_compress(sample_image, quality=50, strip_metadata=True)
    assert result["success"] is True

def test_smoke_diff(sample_image, sample_image2):
    from mcp_raster.server import raster_diff
    result = raster_diff(sample_image, sample_image2)
    assert result["success"] is True

def test_smoke_histogram(sample_image):
    from mcp_raster.server import raster_histogram
    result = raster_histogram(sample_image, channel="r")
    assert result["success"] is True

def test_smoke_edge(sample_image):
    from mcp_raster.server import raster_edge
    result = raster_edge(sample_image, low_threshold=50, high_threshold=150)
    assert result["success"] is True

def test_smoke_blend(sample_image, sample_image2):
    from mcp_raster.server import raster_blend
    result = raster_blend(sample_image, sample_image2, alpha=0.5)
    assert result["success"] is True

def test_smoke_contours(sample_image):
    from mcp_raster.server import raster_contours
    result = raster_contours(sample_image)
    assert result["success"] is True

def test_smoke_exif(sample_jpeg):
    from mcp_raster.server import raster_exif
    result = raster_exif(sample_jpeg)
    assert result["success"] is True
    assert "exif" in result or "data" in result

def test_smoke_colorspace(sample_image):
    from mcp_raster.server import raster_colorspace
    result = raster_colorspace(sample_image, target="HSV")
    assert result["success"] is True

def test_smoke_qr(tmp_path):
    from mcp_raster.server import raster_qr
    # Generate a QR-like image — qr won't decode random image, just check no crash
    img = Image.new("RGB", (200, 200), color="white")
    path = tmp_path / "noqr.png"
    img.save(path)
    result = raster_qr(path)
    # May fail to decode but shouldn't crash
    assert "success" in result

def test_smoke_bgremove(sample_image):
    from mcp_raster.server import raster_bgremove
    result = raster_bgremove(sample_image)
    # bgremove may fail if rembg not installed, just check no crash
    assert "success" in result
