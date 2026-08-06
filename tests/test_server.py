"""Tests for mcp_raster MCP server tools."""

import pytest
import os
from pathlib import Path
from PIL import Image


@pytest.fixture
def sample_image(tmp_path):
    """Create a simple test image."""
    img = Image.new("RGB", (100, 50), color="red")
    path = tmp_path / "sample.png"
    img.save(path)
    return str(path)


@pytest.fixture
def sample_rgba_image(tmp_path):
    """Create an RGBA test image."""
    img = Image.new("RGBA", (100, 50), color=(255, 0, 0, 128))
    path = tmp_path / "sample_rgba.png"
    img.save(path)
    return str(path)


# ---------------------------------------------------------------------------
# raster_info
# ---------------------------------------------------------------------------

def test_raster_info_returns_metadata(sample_image):
    from mcp_raster.server import raster_info
    result = raster_info(sample_image)
    assert result["success"] is True
    assert result["width"] == 100
    assert result["height"] == 50
    assert result["format"] == "PNG"
    assert result["mode"] == "RGB"
    assert result["channels"] == 3


def test_raster_info_file_not_found():
    from mcp_raster.server import raster_info
    result = raster_info("/nonexistent/image.png")
    assert result["success"] is False
    assert result["error"] == "ENOENT"


# ---------------------------------------------------------------------------
# raster_convert
# ---------------------------------------------------------------------------

def test_raster_convert_to_jpeg(sample_image):
    from mcp_raster.server import raster_convert
    result = raster_convert(sample_image, "jpeg")
    assert result["success"] is True
    assert result["format"] == "jpeg"
    assert os.path.isfile(result["output_path"])


def test_raster_convert_to_webp(sample_image):
    from mcp_raster.server import raster_convert
    result = raster_convert(sample_image, "webp", quality=80)
    assert result["success"] is True
    assert result["format"] == "webp"


def test_raster_convert_rgba_to_jpeg(sample_rgba_image):
    from mcp_raster.server import raster_convert
    result = raster_convert(sample_rgba_image, "jpeg")
    assert result["success"] is True
    out = Image.open(result["output_path"])
    assert out.mode == "RGB"


def test_raster_convert_unsupported_format(sample_image):
    from mcp_raster.server import raster_convert
    result = raster_convert(sample_image, "gif")
    assert result["success"] is False
    assert result["error"] == "EUNSUPPORTED"


# ---------------------------------------------------------------------------
# raster_resize
# ---------------------------------------------------------------------------

def test_raster_resize_by_dimensions(sample_image):
    from mcp_raster.server import raster_resize
    result = raster_resize(sample_image, width=50, height=25)
    assert result["success"] is True
    assert result["width"] == 50
    assert result["height"] == 25


def test_raster_resize_by_scale(sample_image):
    from mcp_raster.server import raster_resize
    result = raster_resize(sample_image, scale=0.5)
    assert result["success"] is True
    assert result["width"] == 50
    assert result["height"] == 25


def test_raster_resize_width_only(sample_image):
    from mcp_raster.server import raster_resize
    result = raster_resize(sample_image, width=50)
    assert result["success"] is True
    assert result["width"] == 50
    assert result["height"] == 25  # aspect ratio preserved


# ---------------------------------------------------------------------------
# raster_crop
# ---------------------------------------------------------------------------

def test_raster_crop_rectangle(sample_image):
    from mcp_raster.server import raster_crop
    result = raster_crop(sample_image, left=10, top=10, right=50, bottom=40)
    assert result["success"] is True
    assert result["crop_rect"] == [10, 10, 50, 40]


# ---------------------------------------------------------------------------
# raster_rotate
# ---------------------------------------------------------------------------

def test_raster_rotate_90(sample_image):
    from mcp_raster.server import raster_rotate
    result = raster_rotate(sample_image, degrees=90)
    assert result["success"] is True
    assert os.path.isfile(result["output_path"])


# ---------------------------------------------------------------------------
# raster_adjust
# ---------------------------------------------------------------------------

def test_raster_adjust_brightness(sample_image):
    from mcp_raster.server import raster_adjust
    result = raster_adjust(sample_image, brightness=1.5)
    assert result["success"] is True


def test_raster_adjust_gamma(sample_image):
    """Gamma correction preserves color ratios on pure-color image."""
    from mcp_raster.server import raster_adjust
    import numpy as np

    result = raster_adjust(sample_image, gamma=2.2)
    assert result["success"] is True

    out = Image.open(result["output_path"])
    arr = np.array(out)

    mean_r = arr[:, :, 0].mean()
    mean_g = arr[:, :, 1].mean()
    mean_b = arr[:, :, 2].mean()

    # Red channel dominant (pure red input)
    assert mean_r > mean_g, f"R={mean_r:.0f} should be > G={mean_g:.0f}"
    assert mean_r > mean_b, f"R={mean_r:.0f} should be > B={mean_b:.0f}"
    assert mean_g < 10, f"G={mean_g:.0f} should be near 0 for pure red after gamma"
    assert mean_b < 10, f"B={mean_b:.0f} should be near 0 for pure red after gamma"


# ---------------------------------------------------------------------------
# raster_filter
# ---------------------------------------------------------------------------

def test_raster_filter_grayscale(sample_image):
    from mcp_raster.server import raster_filter
    result = raster_filter(sample_image, "grayscale")
    assert result["success"] is True
    assert result["filter_applied"] == "grayscale"


def test_raster_filter_blur(sample_image):
    from mcp_raster.server import raster_filter
    result = raster_filter(sample_image, "blur")
    assert result["success"] is True


def test_raster_filter_unknown(sample_image):
    from mcp_raster.server import raster_filter
    result = raster_filter(sample_image, "nonexistent")
    assert result["success"] is False
    assert result["error"] == "EUNSUPPORTED"


# ---------------------------------------------------------------------------
# raster_enhance
# ---------------------------------------------------------------------------

def test_raster_enhance_contrast(sample_image):
    from mcp_raster.server import raster_enhance
    result = raster_enhance(sample_image, mode="contrast", factor=2.0)
    assert result["success"] is True


def test_raster_enhance_all(sample_image):
    from mcp_raster.server import raster_enhance
    result = raster_enhance(sample_image, mode="all")
    assert result["success"] is True


def test_raster_enhance_unknown_mode(sample_image):
    from mcp_raster.server import raster_enhance
    result = raster_enhance(sample_image, mode="nonexistent")
    assert result["success"] is False
