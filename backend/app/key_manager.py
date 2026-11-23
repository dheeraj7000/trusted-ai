"""Application-wide KeyManager singleton.

Both receipts and benchmarks use this so all signatures are
verifiable through the /verify endpoint.
"""
import os

from app.evidence.signing import KeyManager

_key_manager: KeyManager | None = None


def get_key_manager() -> KeyManager:
    """Return the shared KeyManager, creating one on first call."""
    global _key_manager
    if _key_manager is None:
        kms_key_id = os.environ.get("AGENTPROOF_KMS_KEY_ID")
        if kms_key_id:
            _key_manager = KeyManager.from_kms(kms_key_id)
        else:
            _key_manager = KeyManager.generate_dev_key()
    return _key_manager
