"""Verification endpoint for proof receipts."""
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.evidence.receipt import verify_receipt
from app.key_manager import get_key_manager
from app.models import ProofReceipt
from app.routes.receipts import RECEIPTS

router = APIRouter()


class VerifyRequest(BaseModel):
    receipt: ProofReceipt | None = None
    receipt_id: str | None = None


@router.post("/verify")
def verify(body: VerifyRequest) -> dict[str, Any]:
    """Verify a proof receipt's integrity and signature."""
    receipt = body.receipt
    if receipt is None:
        if body.receipt_id is None:
            raise HTTPException(
                status_code=400, detail="Provide either receipt or receipt_id"
            )
        receipt = RECEIPTS.get(body.receipt_id)
        if receipt is None:
            raise HTTPException(
                status_code=404, detail=f"Receipt {body.receipt_id} not found"
            )

    km = get_key_manager()
    result = verify_receipt(receipt, km)
    return result
