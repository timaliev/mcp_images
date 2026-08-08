"""ImageMagick backend via Wand — peer to PillowBackend."""

import os

from wand.image import Image
from wand.exceptions import WandException

from mcp_raster._core import _load_image, _output_path
from mcp_raster.backends.base import RasterBackend


def _handle_wand_error(path: str) -> dict | None:
    """Check file existence (Wand doesn't give great errors for missing files)."""
    if not os.path.isfile(path):
        return {"success": False, "error": "ENOENT", "detail": f"File not found: {path}"}
    return None


class MagickBackend(RasterBackend):
    name = "magick"

    # ------------------------------------------------------------------
    # info
    # ------------------------------------------------------------------
    def info(self, path: str) -> dict:
        err = _handle_wand_error(path)
        if err:
            return err
        try:
            with Image(filename=path) as img:
                return {
                    "success": True,
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": "TODO",  # Wand doesn't expose mode like Pillow
                    "dpi": (img.resolution[0] if img.resolution else None),
                    "filesize": os.path.getsize(path),
                    "channels": len(img.channel_images) if hasattr(img, 'channel_images') else 3,
                }
        except WandException as e:
            return {"success": False, "error": "EPROCESSING", "detail": str(e)}

    # ------------------------------------------------------------------
    # convert
    # ------------------------------------------------------------------
    _SUPPORTED_FORMATS = {"png", "jpeg", "webp", "tiff", "bmp", "heic", "avif", "gif"}

    def convert(self, path: str, fmt: str, quality: int = 85, output: str | None = None) -> dict:
        err = _handle_wand_error(path)
        if err:
            return err
        fmt = fmt.lower()
        if fmt not in self._SUPPORTED_FORMATS:
            return {"success": False, "error": "EUNSUPPORTED", "detail": f"Unsupported format: {fmt}"}

        try:
            with Image(filename=path) as img:
                img.format = fmt
                if fmt == "jpeg":
                    img.compression_quality = quality
                elif fmt == "webp":
                    img.compression_quality = quality
                out = output or _output_path(path, fmt if fmt != "jpeg" else "jpg")
                img.save(filename=out)
                return {"success": True, "output_path": out, "format": fmt, "size": os.path.getsize(out)}
        except WandException as e:
            return {"success": False, "error": "EPROCESSING", "detail": str(e)}

    # ------------------------------------------------------------------
    # resize
    # ------------------------------------------------------------------
    def resize(self, path: str, width: int | None = None, height: int | None = None,
               scale: float | None = None, fit: str | None = None, output: str | None = None) -> dict:
        err = _handle_wand_error(path)
        if err:
            return err

        try:
            with Image(filename=path) as img:
                if scale and width is None and height is None:
                    width = int(img.width * scale)
                    height = int(img.height * scale)
                if not width and not height:
                    width, height = img.width, img.height
                elif width and not height:
                    height = int(img.height * (width / img.width))
                elif height and not width:
                    width = int(img.width * (height / img.height))

                if fit == "contain":
                    img.transform(resize=f"{width}x{height}>")
                elif fit == "cover":
                    img.transform(resize=f"{width}x{height}^")
                    img.crop(0, 0, width, height)
                else:
                    img.resize(width, height, filter="lanczos")

                out = output or _output_path(path)
                img.save(filename=out)
                return {"success": True, "output_path": out, "width": img.width, "height": img.height}
        except WandException as e:
            return {"success": False, "error": "EPROCESSING", "detail": str(e)}

    # ------------------------------------------------------------------
    # crop
    # ------------------------------------------------------------------
    def crop(self, path: str, left: int, top: int, right: int, bottom: int,
             output: str | None = None) -> dict:
        err = _handle_wand_error(path)
        if err:
            return err
        try:
            with Image(filename=path) as img:
                img.crop(left, top, right, bottom)
                out = output or _output_path(path, "crop")
                img.save(filename=out)
                return {"success": True, "output_path": out, "crop_rect": [left, top, right, bottom]}
        except WandException as e:
            return {"success": False, "error": "EPROCESSING", "detail": str(e)}

    # ------------------------------------------------------------------
    # rotate
    # ------------------------------------------------------------------
    def rotate(self, path: str, degrees: float, expand: bool = True,
               output: str | None = None) -> dict:
        err = _handle_wand_error(path)
        if err:
            return err
        try:
            with Image(filename=path) as img:
                # Wand rotates around center by default
                if expand:
                    img.rotate(degrees)
                else:
                    img.rotate(degrees)
                out = output or _output_path(path)
                img.save(filename=out)
                return {"success": True, "output_path": out}
        except WandException as e:
            return {"success": False, "error": "EPROCESSING", "detail": str(e)}

    # ------------------------------------------------------------------
    # adjust
    # ------------------------------------------------------------------
    def adjust(self, path: str, brightness: float | None = None, contrast: float | None = None,
               saturation: float | None = None, sharpness: float | None = None,
               gamma: float | None = None, output: str | None = None) -> dict:
        err = _handle_wand_error(path)
        if err:
            return err
        try:
            with Image(filename=path) as img:
                if brightness is not None:
                    img.brightness_contrast(brightness=brightness * 100 - 100)
                if contrast is not None:
                    img.brightness_contrast(contrast=contrast * 100 - 100)
                if saturation is not None:
                    img.modulate(saturation=saturation * 100)
                if sharpness is not None:
                    # Wand unsharp_mask(radius, sigma, amount, threshold)
                    amount = (sharpness - 1.0) * 2.0
                    if amount > 0:
                        img.unsharp_mask(radius=0.5, sigma=0.5, amount=amount, threshold=0)
                if gamma is not None:
                    img.gamma(gamma)
                out = output or _output_path(path)
                img.save(filename=out)
                return {"success": True, "output_path": out}
        except WandException as e:
            return {"success": False, "error": "EPROCESSING", "detail": str(e)}
