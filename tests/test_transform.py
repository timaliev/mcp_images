"""Tests for raster transform tools."""

import pytest
import os
from PIL import Image


@pytest.fixture
def sample_image(tmp_path):
    img = Image.new("RGB", (200, 100), color="white")
    # Draw something recognizable so transforms are visible
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 20, 150, 80], fill="blue")
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


def test_raster_perspective_bad_points(sample_image):
    from mcp_raster.transform import raster_perspective
    # Only 3 points instead of 4
    result = raster_perspective(sample_image, [[0, 0], [10, 0], [10, 10]], [[0, 0], [10, 0], [10, 10]])
    assert result["success"] is False
    assert result["error"] == "EPROCESSING"


def test_raster_perspective_file_not_found():
    from mcp_raster.transform import raster_perspective
    src = [[0, 0], [10, 0], [10, 10], [0, 10]]
    dst = [[0, 0], [10, 0], [10, 10], [0, 10]]
    result = raster_perspective("/nonexistent/img.png", src, dst)
    assert result["success"] is False
    assert result["error"] == "ENOENT"


# --- raster_morphology ---

def test_raster_morphology_dilate(sample_image):
    from mcp_raster.transform import raster_morphology
    result = raster_morphology(sample_image, operation="dilate")
    assert result["success"] is True
    assert os.path.isfile(result["output_path"])


def test_raster_morphology_erode(sample_image):
    from mcp_raster.transform import raster_morphology
    result = raster_morphology(sample_image, operation="erode")
    assert result["success"] is True


def test_raster_morphology_open(sample_image):
    from mcp_raster.transform import raster_morphology
    result = raster_morphology(sample_image, operation="open")
    assert result["success"] is True


def test_raster_morphology_close(sample_image):
    from mcp_raster.transform import raster_morphology
    result = raster_morphology(sample_image, operation="close")
    assert result["success"] is True


def test_raster_morphology_unknown_op(sample_image):
    from mcp_raster.transform import raster_morphology
    result = raster_morphology(sample_image, operation="skeletonize")
    assert result["success"] is False
    assert result["error"] == "EUNSUPPORTED"


# --- raster_balance ---

def test_raster_balance_equalize(sample_image):
    from mcp_raster.transform import raster_balance
    result = raster_balance(sample_image, mode="equalize")
    assert result["success"] is True
    assert os.path.isfile(result["output_path"])


def test_raster_balance_autocontrast(sample_image):
    from mcp_raster.transform import raster_balance
    result = raster_balance(sample_image, mode="autocontrast")
    assert result["success"] is True


def test_raster_balance_auto_white(sample_image):
    from mcp_raster.transform import raster_balance
    result = raster_balance(sample_image, mode="auto_white")
    assert result["success"] is True


def test_raster_balance_unknown_mode(sample_image):
    from mcp_raster.transform import raster_balance
    result = raster_balance(sample_image, mode="clahe")
    assert result["success"] is False
    assert result["error"] == "EUNSUPPORTED"


# --- raster_padding ---

def test_raster_padding_add_border(sample_image):
    from mcp_raster.transform import raster_padding
    result = raster_padding(sample_image, top=10, right=10, bottom=10, left=10, fill_color="black")
    assert result["success"] is True
    assert result["width"] == 220  # 200 + 10 + 10
    assert result["height"] == 120  # 100 + 10 + 10


def test_raster_padding_zero_padding(sample_image):
    from mcp_raster.transform import raster_padding
    result = raster_padding(sample_image)
    assert result["success"] is True
    # No padding means same size
    assert result["width"] == 200
    assert result["height"] == 100


# --- raster_channels ---

def test_raster_channels_extract_red(sample_image):
    from mcp_raster.transform import raster_channels
    result = raster_channels(sample_image, operation="extract", channels=[0])
    assert result["success"] is True
    assert os.path.isfile(result["output_path"])
    out = Image.open(result["output_path"])
    assert out.mode == "L"  # single channel extracted


def test_raster_channels_swap(sample_image):
    from mcp_raster.transform import raster_channels
    result = raster_channels(sample_image, operation="swap", channels=[0, 2])
    assert result["success"] is True


def test_raster_channels_unknown_op(sample_image):
    from mcp_raster.transform import raster_channels
    result = raster_channels(sample_image, operation="quantize")
    assert result["success"] is False
    assert result["error"] == "EUNSUPPORTED"


# --- raster_compress ---

@pytest.fixture
def large_noisy_image(tmp_path):
    """Larger image with noise so JPEG compression actually reduces size."""
    import numpy as np
    arr = np.random.randint(0, 256, (400, 400, 3), dtype=np.uint8)
    img = Image.fromarray(arr)
    path = tmp_path / "noisy.png"
    img.save(path)
    return str(path)


def test_raster_compress_reduces_size(large_noisy_image):
    from mcp_raster.transform import raster_compress
    result = raster_compress(large_noisy_image, quality=10)
    assert result["success"] is True
    assert result["output_path"].endswith(".jpg")
    assert os.path.getsize(result["output_path"]) < os.path.getsize(large_noisy_image)


def test_raster_compress_file_not_found():
    from mcp_raster.transform import raster_compress
    result = raster_compress("/nonexistent/img.png")
    assert result["success"] is False
    assert result["error"] == "ENOENT"


def test_raster_compress_with_custom_output(large_noisy_image, tmp_path):
    from mcp_raster.transform import raster_compress
    out_path = str(tmp_path / "custom_compressed.jpg")
    result = raster_compress(large_noisy_image, quality=50, output=out_path)
    assert result["success"] is True
    assert result["output_path"] == out_path
    assert os.path.isfile(out_path)
