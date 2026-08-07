# Development — mcp_images

## Setup

```bash
git clone https://github.com/timaliev/mcp_images.git
cd mcp_images
uv sync
```

## Test runner

```bash
uv run pytest
```

## Linting & formatting

```bash
uv run ruff check .          # lint
uv run ruff check --fix .    # auto-fix
uv run ruff format .         # format
```

## Git workflow

- NEVER work directly on `develop` or `master`
- Create feature branch from `develop`: `git checkout -b feat/my-feature develop`
- Commit using [conventional commits](https://www.conventionalcommits.org/)
- Open PR to `develop`
- Release: merge `develop` → `release` → PR → `master` (GitHub Actions handles tags + CHANGELOG)
