"""Abstract backend interface for raster operations."""

from abc import ABC, abstractmethod


class RasterBackend(ABC):
    """Base class for raster manipulation backends (Pillow, ImageMagick, etc.)."""

    name: str

    @abstractmethod
    def info(self, path: str) -> dict: ...
    @abstractmethod
    def convert(self, path: str, fmt: str, quality: int = 85, output: str | None = None) -> dict: ...
    @abstractmethod
    def resize(self, path: str, width: int | None = None, height: int | None = None,
               scale: float | None = None, fit: str | None = None, output: str | None = None) -> dict: ...
    @abstractmethod
    def crop(self, path: str, left: int, top: int, right: int, bottom: int,
             output: str | None = None) -> dict: ...
    @abstractmethod
    def rotate(self, path: str, degrees: float, expand: bool = True,
               output: str | None = None) -> dict: ...
    @abstractmethod
    def adjust(self, path: str, brightness: float | None = None, contrast: float | None = None,
               saturation: float | None = None, sharpness: float | None = None,
               gamma: float | None = None, output: str | None = None) -> dict: ...
