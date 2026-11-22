"""Tool execution endpoints."""
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException

from app.models import DataSendRequest, RefundRequest, ToolResult
from app.routes.runs import RUNS
from app.telemetry.tracing import get_tracer
from app.tools.data_send import execute_data_send
from app.tools.refund import execute_refund

router = APIRouter()
tracer = get_tracer()


def _parameters_match(evaluated_params: dict[str, Any], tool_params: dict[str, Any]) -> bool:
    """Check that the approval covers the parameters being executed.

    Every key in tool_params must exist in evaluated_params with the same
    value. This prevents an empty-params evaluation from approving
    arbitrary tool executions.
    """
    for key, value in tool_params.items():
        if key not in evaluated_params or evaluated_params[key] != value:
            return False
    return True


def _check_policy_approval(run_id: str, action_type: str, tool_params: dict[str, Any]) -> None:
    """Verify that the action was evaluated and allowed by the policy engine.

    Matches on action_type and overlapping parameters, then consumes the
    approval so it cannot be reused for a different execution.
    """
    run = RUNS.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    # Look for a matching, unconsumed ALLOW decision in the run's events
    for event in run.events:
        if (
            event.get("type") == "policy_decision"
            and event.get("action_type") == action_type
            and event.get("decision") == "ALLOW"
            and not event.get("consumed")
        ):
            evaluated_params = event.get("parameters", {})
            if _parameters_match(evaluated_params, tool_params):
                event["consumed"] = True
                return
    raise HTTPException(
        status_code=403,
        detail=f"No matching ALLOW policy decision found for action '{action_type}' in run {run_id}. "
        "Evaluate the action first via POST /actions/evaluate.",
    )


@router.post("/tools/refund", response_model=ToolResult)
def tool_refund(body: RefundRequest) -> ToolResult:
    """Execute a refund tool call."""
    _check_policy_approval(body.run_id, "refund", {"amount": body.amount, "order_id": body.order_id})
    with tracer.start_as_current_span(
        "tool.refund", attributes={"run_id": body.run_id}
    ) as span:
        result = execute_refund(body)
        span.set_attribute("success", result.success)
    # Record tool execution event
    run = RUNS.get(body.run_id)
    if run is not None:
        run.events.append({
            "type": "tool_executed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool": "refund",
            "result": result.model_dump(),
        })
    return result


@router.post("/tools/data-send", response_model=ToolResult)
def tool_data_send(body: DataSendRequest) -> ToolResult:
    """Execute a data send tool call."""
    _check_policy_approval(body.run_id, "data_send", {
        "destination": body.destination,
        "payload": body.payload,
        "content_type": body.content_type,
    })
    with tracer.start_as_current_span(
        "tool.data_send", attributes={"run_id": body.run_id}
    ) as span:
        result = execute_data_send(body)
        span.set_attribute("success", result.success)
    # Record tool execution event
    run = RUNS.get(body.run_id)
    if run is not None:
        run.events.append({
            "type": "tool_executed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool": "data_send",
            "result": result.model_dump(),
        })
    return result
