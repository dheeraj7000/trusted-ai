"""Refund tool implementation."""

from app.fixtures import get_order
from app.models import RefundRequest, ToolResult


def execute_refund(request: RefundRequest) -> ToolResult:
    """Execute a refund for the given order."""
    order = get_order(request.order_id)
    if order is None:
        return ToolResult(
            tool="refund",
            success=False,
            result={"error": f"Order {request.order_id} not found"},
            blocked=False,
            reason="Order not found",
        )

    return ToolResult(
        tool="refund",
        success=True,
        result={
            "order_id": request.order_id,
            "refund_amount": request.amount,
            "original_amount": order.amount,
            "status": "refunded",
        },
        blocked=False,
    )
