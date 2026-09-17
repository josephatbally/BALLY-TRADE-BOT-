"""BALLY FLOW environment loading.

Loads local development configuration without overriding real process
environment variables. Secrets are never logged.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable


def _candidate_files() -> Iterable[Path]:
    root = Path(__file__).resolve().parents[2]
    yield root / ".env"
    yield root / "backend" / ".env"


def load_local_env() -> None:
    """Load simple KEY=VALUE pairs from the local .env files if present.

    Existing process environment variables always win. This intentionally
    supports the project's simple .env format without adding a runtime
    dependency just for development configuration.
    """
    for env_path in _candidate_files():
        if not env_path.is_file():
            continue
        try:
            lines = env_path.read_text(encoding="utf-8-sig").splitlines()
        except OSError:
            continue

        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if not key or key in os.environ:
                continue
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            os.environ[key] = value


load_local_env()
