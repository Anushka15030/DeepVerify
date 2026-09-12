"""Tests for filesystem storage service."""

from __future__ import annotations

import pytest

from app.services.storage import FileStorage


def test_write_and_read_json(tmp_storage_dir) -> None:
    storage = FileStorage(base_dir=tmp_storage_dir)
    payload = {"topic": "test", "count": 2}
    storage.write_json("runs/run-1.json", payload)
    assert storage.read_json("runs/run-1.json") == payload


def test_write_and_read_bytes(tmp_storage_dir) -> None:
    storage = FileStorage(base_dir=tmp_storage_dir)
    data = b"binary-content"
    storage.write_bytes("artifacts/file.bin", data)
    assert storage.read_bytes("artifacts/file.bin") == data


def test_exists_and_delete(tmp_storage_dir) -> None:
    storage = FileStorage(base_dir=tmp_storage_dir)
    storage.write_json("temp.json", {"ok": True})
    assert storage.exists("temp.json") is True
    assert storage.delete("temp.json") is True
    assert storage.exists("temp.json") is False
    assert storage.delete("temp.json") is False


def test_rejects_empty_key(tmp_storage_dir) -> None:
    storage = FileStorage(base_dir=tmp_storage_dir)
    with pytest.raises(ValueError, match="must not be empty"):
        storage.write_json("  ", {})


def test_rejects_path_traversal(tmp_storage_dir) -> None:
    storage = FileStorage(base_dir=tmp_storage_dir)
    with pytest.raises(ValueError, match="outside base directory"):
        storage.write_json("../escape.json", {"bad": True})
