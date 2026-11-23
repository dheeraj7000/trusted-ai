"""Action evaluation endpoints."""
from datetime import datetime, timezone

from fastapi import APIRouter

from app.models import ActionEvaluateRequest, PolicyDecision
from app.routes.runs import RUNS
from app.telemetry.tracing import get_tracer

router = APIRouter()
tracer = get_tracer()


@router.post("/actions/evaluate", response_model=PolicyDecision)
def evaluate_action(body: ActionEvaluateRequest) -> PolicyDecision:
    """Evaluate an action against the policy engine."""
    from app.main import policy_engine

    with tracer.start_as_current_span(
        "policy.evaluate",
        attributes={"run_id": body.run_id, "action_type": body.action_type},
    ) as span:
        decision = policy_engine.evaluate(body)
        span.set_attribute("decision", decision.decision)
        span.set_attribute("reason", decision.reason)

    # Record decision event in the run if it exists
    run = RUNS.get(body.run_id)
    if run is not None:
        run.events.append({
            "type": "policy_decision",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action_type": body.action_type,
            "parameters": body.parameters,
            "decision": decision.decision,
            "reason": decision.reason,
        })
    return decision
