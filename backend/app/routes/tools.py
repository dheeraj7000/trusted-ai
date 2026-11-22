"""Tool execution endpoints."""
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.models import DataSendRequest, RefundRequest, ToolResult
from app.routes.runs import RUNS
from app.telemetry.tracing import get_tracer
from app.tools.data_send import execute_data_send
from app.tools.refund import execute_refund

router = APIRouter()

tracer = get_tracer()


def _check_policy_approval(run_id: str, action_type: str) -> None:
    """Verify that the action was evaluated and allowed by the policy engine."""
    run = RUNS.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    # Look for a matching ALLOW decision in the run's events
    for event in run.events:
        if (
            event.get("type") == "policy_decision"
            and event.get("action_type") == action_type
            and event.get("decision") == "ALLOW"
        ):
            return

    raise HTTPException(
        status_code=403,
        detail=f"No ALLOW policy decision found for action '{action_type}' in run {run_id}. "
        "Evaluate the action first via POST /actions/evaluate.",
    )


@router.post("/tools/refund", response_model=ToolResult)
def tool_refund(body: RefundRequest) -> ToolResult:
    """Execute a refund tool call."""
    _check_policy_approval(body.run_id, "refund")

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
            "timestamp": datetime.utcnow().isoformat(),
            "tool": "refund",
            "result": result.model_dump(),
        })

    return result


@router.post("/tools/data-send", response_model=ToolResult)
def tool_data_send(body: DataSendRequest) -> ToolResult:
    """Execute a data send tool call."""
    _check_policy_approval(body.run_id, "data_send")

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
            "timestamp": datetime.utcnow().isoformat(),
            "tool": "data_send",
            "result": result.model_dump(),
        })

    return result
