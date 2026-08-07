"""Tests for raster metadata tools."""

import pytest
import os
from PIL import Image


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
    assert result["colorspace"] == "HSV"
    assert os.path.isfile(result["output_path"])


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
    # Implementation auto-resizes to match
    result = raster_blend(sample_image, str(big_path), alpha=0.5)
    assert result["success"] is True
    assert os.path.isfile(result["output_path"])


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
