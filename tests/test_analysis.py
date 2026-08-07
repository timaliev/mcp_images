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
