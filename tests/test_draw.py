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
