"""Tests for MagickBackend via Wand/ImageMagick."""

import pytest
import os
from PIL import Image as PILImage


@pytest.fixture
def sample_image(tmp_path):
    img = PILImage.new("RGB", (100, 50), color="red")
    path = tmp_path / "sample.png"
    img.save(path)
    return str(path)


@pytest.fixture
def magick():
    from mcp_raster.backends.magick import MagickBackend
    return MagickBackend()


# ---------------------------------------------------------------------------
# info
# ---------------------------------------------------------------------------

def test_magick_info_returns_metadata(magick, sample_image):
    result = magick.info(sample_image)
    assert result["success"] is True
    assert result["width"] == 100
    assert result["height"] == 50
    assert "format" in result
    assert "filesize" in result


def test_magick_info_file_not_found(magick):
    result = magick.info("/nonexistent/img.png")
    assert result["success"] is False
    assert result["error"] == "ENOENT"


# ---------------------------------------------------------------------------
# convert
# ---------------------------------------------------------------------------

def test_magick_convert_to_jpeg(magick, sample_image):
    result = magick.convert(sample_image, "jpeg", quality=85)
    assert result["success"] is True
    assert result["format"] == "jpeg"
    assert os.path.isfile(result["output_path"])


def test_magick_convert_to_webp(magick, sample_image):
    result = magick.convert(sample_image, "webp")
    assert result["success"] is True
    assert result["format"] == "webp"


def test_magick_convert_unsupported_format(magick, sample_image):
    result = magick.convert(sample_image, "xyz")
    assert result["success"] is False
    assert result["error"] == "EUNSUPPORTED"


# ---------------------------------------------------------------------------
# resize
# ---------------------------------------------------------------------------

def test_magick_resize_by_dimensions(magick, sample_image):
    result = magick.resize(sample_image, width=50, height=25)
    assert result["success"] is True
    assert result["width"] == 50
    assert result["height"] == 25


def test_magick_resize_by_scale(magick, sample_image):
    result = magick.resize(sample_image, scale=0.5)
    assert result["success"] is True
    assert result["width"] == 50
    assert result["height"] == 25


# ---------------------------------------------------------------------------
# crop
# ---------------------------------------------------------------------------

def test_magick_crop_rectangle(magick, sample_image):
    result = magick.crop(sample_image, left=10, top=10, right=50, bottom=40)
    assert result["success"] is True
    assert result["crop_rect"] == [10, 10, 50, 40]


# ---------------------------------------------------------------------------
# rotate
# ---------------------------------------------------------------------------

def test_magick_rotate_90(magick, sample_image):
    result = magick.rotate(sample_image, degrees=90)
    assert result["success"] is True
    assert os.path.isfile(result["output_path"])


# ---------------------------------------------------------------------------
# adjust
# ---------------------------------------------------------------------------

def test_magick_adjust_brightness(magick, sample_image):
    result = magick.adjust(sample_image, brightness=1.5)
    assert result["success"] is True


def test_magick_adjust_contrast(magick, sample_image):
    result = magick.adjust(sample_image, contrast=1.2)
    assert result["success"] is True
