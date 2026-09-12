"""Filesystem-backed storage service."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.core.config import Settings, get_settings

_UNSAFE_KEY_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


class FileStorage:
    """Store and retrieve artifacts on the local filesystem."""

    def __init__(self, settings: Settings | None = None, base_dir: Path | str | None = None) -> None:
        cfg = settings or get_settings()
        self.base_dir = Path(base_dir or cfg.storage_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, key: str) -> Path:
        if not key or not key.strip():
            raise ValueError("Storage key must not be empty")

        raw = key.strip()
        if ".." in Path(raw).parts:
            raise ValueError("Storage key resolves outside base directory")

        sanitized = _UNSAFE_KEY_PATTERN.sub("_", raw)
        if sanitized in {".", ".."}:
            raise ValueError("Invalid storage key")

        target = (self.base_dir / sanitized).resolve()
        if target != self.base_dir and self.base_dir not in target.parents:
            raise ValueError("Storage key resolves outside base directory")
        return target

    def write_json(self, key: str, data: Any) -> Path:
        path = self._resolve_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        return path

    def read_json(self, key: str) -> Any:
        path = self._resolve_path(key)
        if not path.exists():
            raise FileNotFoundError(f"Storage key not found: {key}")
        return json.loads(path.read_text(encoding="utf-8"))

    def write_bytes(self, key: str, data: bytes) -> Path:
        path = self._resolve_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def read_bytes(self, key: str) -> bytes:
        path = self._resolve_path(key)
        if not path.exists():
            raise FileNotFoundError(f"Storage key not found: {key}")
        return path.read_bytes()

    def exists(self, key: str) -> bool:
        return self._resolve_path(key).exists()

    def delete(self, key: str) -> bool:
        path = self._resolve_path(key)
        if not path.exists():
            return False
        path.unlink()
        return True
