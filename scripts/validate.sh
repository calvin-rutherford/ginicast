#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# A separate environment preserves any existing .venv/.
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-.venv-validation}"
uv sync --locked --extra dev
uv run --locked --extra dev ruff check src tests scripts
uv run --locked --extra dev pytest -q
uv run --locked --extra dev python scripts/demo.py
