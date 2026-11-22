"""Receipt management endpoints."""
from fastapi import APIRouter, HTTPException

from app.evidence.receipt import build_receipt
from app.evidence.signing import KeyManager
from app.fixtures import DEFAULT_POLICY
from app.models import ProofReceipt
from app.routes.runs import RUNS

router = APIRouter()

# In-memory receipt storage
RECEIPTS: dict[str, ProofReceipt] = {}

# Module-level key manager (initialized on first use)
_key_manager: KeyManager | None = None


def _get_key_manager() -> KeyManager:
    global _key_manager
    if _key_manager is None:
        _key_manager = KeyManager.generate_dev_key()
    return _key_manager


@router.post("/runs/{run_id}/finalize", response_model=ProofReceipt)
def finalize_run(run_id: str) -> ProofReceipt:
    """Build and store a proof receipt for the given run."""
    run = RUNS.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    km = _get_key_manager()
    receipt = build_receipt(run_state=run, policy=DEFAULT_POLICY, key_manager=km)
    RECEIPTS[run_id] = receipt
    return receipt


@router.get("/receipts/{receipt_id}", response_model=ProofReceipt)
def get_receipt(receipt_id: str) -> ProofReceipt:
    """Return a stored receipt by ID (receipt_id = run_id)."""
    receipt = RECEIPTS.get(receipt_id)
    if receipt is None:
        raise HTTPException(status_code=404, detail=f"Receipt {receipt_id} not found")
    return receipt
