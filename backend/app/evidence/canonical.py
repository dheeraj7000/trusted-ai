"""Canonical JSON serialization for deterministic hashing."""
import hashlib
import json
from typing import Any

from pydantic import BaseModel


def _sort_recursive(obj: Any) -> Any:
    """Recursively sort dict keys and list-of-dict contents."""
    if isinstance(obj, dict):
        return {k: _sort_recursive(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [_sort_recursive(item) for item in obj]
    return obj


def canonical_json_serialize(obj: Any) -> bytes:
    """Produce deterministic JSON bytes from a dict or Pydantic model."""
    if isinstance(obj, BaseModel):
        data = obj.model_dump()
    elif isinstance(obj, dict):
        data = obj
    else:
        data = obj
    data = _sort_recursive(data)
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def canonical_json_hash(obj: Any) -> str:
    """Return hex SHA-256 of the canonical JSON bytes."""
    return hashlib.sha256(canonical_json_serialize(obj)).hexdigest()
