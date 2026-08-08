# Backend Abstraction Layer for mcp-image

**Date:** 2026-08-08  
**Status:** Phase 1 — Prototyping

## Overview

Introduce a backend abstraction layer that allows swapping raster processing engines
(Pillow, ImageMagick/Wand) without changing the MCP tool interface.

## Motivation

- Pillow is fast but limited: no HEIC/AVIF/PSD, fixed resize filters, no real unsharp mask
- ImageMagick via Wand adds 40+ resize filters, industry-standard sharpening, 200+ format support
- Both backends should coexist — users choose per-operation via `backend` parameter

## Architecture

```
mcp_raster/
├── backends/              # NEW
│   ├── __init__.py
│   ├── base.py            # RasterBackend (ABC)
│   └── pillow.py          # PillowBackend — moved from server.py
├── _core.py               # shared utils (unchanged)
├── server.py              # thin dispatch + MCP tool registration
├── draw.py, filters.py,
│   transform.py, etc.     # specialized tools (unchanged)
```

### Base class

```python
class RasterBackend(ABC):
    name: str
    def info(path) -> dict: ...
    def convert(path, fmt, quality, output) -> dict: ...
    def resize(path, width, height, scale, fit, output) -> dict: ...
    def crop(path, left, top, right, bottom, output) -> dict: ...
    def rotate(path, degrees, expand, output) -> dict: ...
    def adjust(path, brightness, contrast, saturation, sharpness, gamma, output) -> dict: ...
```

### PillowBackend

Moves the 6 core tool implementations from `server.py` into `backends/pillow.py`.
No behavioral changes — identical logic, same Pillow+OpenCV calls.

### server.py

Thin dispatch: each `@server.tool()` function delegates to `_resolve_backend(backend).method(...)`.

```python
_pillow = PillowBackend()
_backends = {"pillow": _pillow}

@server.tool()
def raster_info(path, backend=None):
    return _resolve_backend(backend).info(path)
```

Each core tool accepts an optional `backend` parameter (default: `"pillow"`).
Specialized tools (draw, transform, metadata, analysis) are unchanged —
they don't accept `backend` yet.

### Backend resolution

```python
def _resolve_backend(backend_name):
    if backend_name is None:
        return _pillow  # default
    return _backends.get(backend_name.lower(), _pillow)  # graceful fallback
```

## Design Principles

1. **Core tools** (info, convert, resize, crop, rotate, adjust): backend-aware, `backend` param
2. **Specialized tools** (draw, text, exif, diff, etc.): no `backend` param yet — Pillow only
3. **Graceful degradation**: if a backend is missing, fall back to Pillow silently or return structured error
4. **Shared interface**: all backends return same `{"success": True, ...}` shape
5. **No circular imports**: backends import from `_core`, server imports from backends

## Phase 2 (planned)

Add `backends/magick.py` with `MagickBackend` implementing `RasterBackend` via Wand.
Core tools gain `backend="magick"` option. New IM-only tools for composite, montage, ICC, FX.

## Phase 3 (planned)

Extend specialized tools with `backend` parameter where IM has advantages
(filter, morphology, histogram, compare).

## Testing

- Existing 59 tests keep passing — backend default unchanged
- Phase 2 adds `tests/test_magick_backend.py`
- No new tests required for Phase 1 (pure refactor, behavior identical)
