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
