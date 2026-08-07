# CONTEXT.md — Glossary for mcp_images

## Domain

- **MCP (Model Context Protocol)** — JSON-RPC protocol connecting AI agents to tools over stdio/SSE
- **Raster** — pixel-based image (vs vector). Operations: resize, crop, rotate, filter, convert
- **Pillow** — Python imaging library (PIL fork), core manipulation backend
- **OpenCV** — Open Source Computer Vision library, used for advanced filters

## Architecture

- `mcp_raster/server.py` — MCP server entry point, registers all raster tools
- Each tool is a standalone function wrapping Pillow/OpenCV operations
- Tools follow naming: `raster_info`, `raster_convert`, `raster_resize`, etc.

## Conventions

- **Language:** Python 3.11+
- **Package manager:** uv / pip
- **Testing:** pytest
- **CI/CD:** GitHub Actions (to be added)
- **Versioning:** semantic via git-cliff
