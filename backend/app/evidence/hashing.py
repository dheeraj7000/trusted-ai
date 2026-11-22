"""Merkle-like hash tree computation for evidence bundles."""
import hashlib

from app.evidence.canonical import canonical_json_hash


def compute_provenance_root(source_objects: list[dict]) -> str:
    """Hash each source object, sort the hashes, concatenate, and SHA-256."""
    hashes = sorted(canonical_json_hash(obj) for obj in source_objects)
    combined = "".join(hashes)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def compute_trace_root(trace_events: list[dict]) -> str:
    """Hash each trace event in order, concatenate, and SHA-256."""
    hashes = [canonical_json_hash(event) for event in trace_events]
    combined = "".join(hashes)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def compute_state_root(state_manifest: dict) -> str:
    """Canonical hash of the state manifest dict."""
    return canonical_json_hash(state_manifest)


def compute_receipt_root(
    run_id: str,
    provenance_root: str,
    trace_root: str,
    state_root: str,
    benchmark_digest: str,
    timestamp: str,
) -> str:
    """SHA-256 of concatenated run_id || P || T || S || benchmark_digest || timestamp."""
    combined = f"{run_id}{provenance_root}{trace_root}{state_root}{benchmark_digest}{timestamp}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()
