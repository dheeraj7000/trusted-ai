"""State manifest builder for evidence bundles."""
import hashlib
import json

from app.models import PolicyConfig, RunState


def build_state_manifest(run_state: RunState, policy: PolicyConfig) -> dict:
    """Build a state manifest capturing the runtime environment snapshot."""
    image_digest = hashlib.sha256("agentproof:dev".encode("utf-8")).hexdigest()

    # Minimal CycloneDX-style SBOM
    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.4",
        "components": [
            {"name": "fastapi", "type": "library"},
            {"name": "uvicorn", "type": "library"},
            {"name": "pydantic", "type": "library"},
            {"name": "cryptography", "type": "library"},
            {"name": "opentelemetry-api", "type": "library"},
            {"name": "opentelemetry-sdk", "type": "library"},
        ],
    }
    sbom_digest = hashlib.sha256(
        json.dumps(sbom, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    # Crypto Bill of Materials
    cbom = {
        "algorithms": ["SHA-256", "ECDSA-P256"],
        "libraries": ["cryptography"],
        "key_references": ["dev_signing_key"],
    }
    cbom_digest = hashlib.sha256(
        json.dumps(cbom, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return {
        "image_digest": image_digest,
        "agent_version": "0.1.0",
        "model_provider": run_state.model_provider,
        "model_id": run_state.model_id,
        "policy_version": policy.policy_version,
        "sbom_digest": sbom_digest,
        "cbom_digest": cbom_digest,
    }
