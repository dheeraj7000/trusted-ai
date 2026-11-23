"""Evidence receipt building and verification."""
from datetime import datetime, timezone
from typing import Any, Optional

from app.evidence.hashing import (
    compute_provenance_root,
    compute_receipt_root,
    compute_state_root,
    compute_trace_root,
)
from app.evidence.signing import KeyManager
from app.evidence.state_manifest import build_state_manifest
from app.models import PolicyConfig, ProofReceipt, RunState


def build_receipt(
    run_state: RunState,
    policy: PolicyConfig,
    key_manager: KeyManager,
    benchmark_id: Optional[str] = None,
    benchmark_score: Optional[float] = None,
) -> ProofReceipt:
    """Build a complete ProofReceipt for a finalized run."""
    # Collect source objects: action requests and tool results from events
    source_objects: list[dict] = []
    for event in run_state.events:
        if event.get("type") in ("action_requested", "tool_executed"):
            source_objects.append(event)

    # Trace events: all events in the run
    trace_events = list(run_state.events)

    # Build state manifest
    state_manifest = build_state_manifest(run_state, policy)

    # Compute roots
    provenance_root = compute_provenance_root(source_objects) if source_objects else compute_provenance_root([{}])
    trace_root = compute_trace_root(trace_events) if trace_events else compute_trace_root([{}])
    state_root = compute_state_root(state_manifest)

    benchmark_digest = ""
    if benchmark_id and benchmark_score is not None:
        import hashlib
        benchmark_digest = hashlib.sha256(
            f"{benchmark_id}:{benchmark_score}".encode("utf-8")
        ).hexdigest()

    timestamp = datetime.now(timezone.utc).isoformat()

    receipt_root = compute_receipt_root(
        run_id=run_state.run_id,
        provenance_root=provenance_root,
        trace_root=trace_root,
        state_root=state_root,
        benchmark_digest=benchmark_digest,
        timestamp=timestamp,
    )

    # Sign
    signature = key_manager.sign(receipt_root)

    return ProofReceipt(
        receipt_version="0.1.0",
        run_id=run_state.run_id,
        timestamp=datetime.fromisoformat(timestamp),
        agent_id=run_state.agent_id,
        agent_version="0.1.0",
        model_provider=run_state.model_provider,
        model_id=run_state.model_id,
        policy_version=policy.policy_version,
        container_image_digest=state_manifest["image_digest"],
        sbom_digest=state_manifest["sbom_digest"],
        cbom_digest=state_manifest["cbom_digest"],
        provenance_root=provenance_root,
        trace_root=trace_root,
        state_root=state_root,
        benchmark_id=benchmark_id,
        benchmark_score=benchmark_score,
        receipt_root=receipt_root,
        signature=signature,
        key_id=key_manager.key_id,
    )


def verify_receipt(receipt: ProofReceipt, key_manager: KeyManager) -> dict[str, Any]:
    """Verify a receipt's integrity and signature.

    Returns a dict with valid, checks, and errors.
    """
    errors: list[str] = []
    checks: dict[str, bool] = {}

    # Recompute receipt root from stored roots
    benchmark_digest = ""
    if receipt.benchmark_id and receipt.benchmark_score is not None:
        import hashlib
        benchmark_digest = hashlib.sha256(
            f"{receipt.benchmark_id}:{receipt.benchmark_score}".encode("utf-8")
        ).hexdigest()

    recomputed_root = compute_receipt_root(
        run_id=receipt.run_id,
        provenance_root=receipt.provenance_root,
        trace_root=receipt.trace_root,
        state_root=receipt.state_root,
        benchmark_digest=benchmark_digest,
        timestamp=receipt.timestamp.isoformat(),
    )

    checks["receipt_root_match"] = recomputed_root == receipt.receipt_root
    if not checks["receipt_root_match"]:
        errors.append("Receipt root does not match recomputed value")

    # Verify signature against receipt root
    checks["signature_valid"] = key_manager.verify_signature(
        receipt.receipt_root, receipt.signature
    )
    if not checks["signature_valid"]:
        errors.append("Signature verification failed")

    valid = all(checks.values())
    return {
        "valid": valid,
        "checks": checks,
        "errors": errors,
    }
