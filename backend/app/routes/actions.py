"""Action evaluation endpoints."""

from datetime import datetime

from fastapi import APIRouter

from app.models import ActionEvaluateRequest, PolicyDecision
from app.routes.runs import RUNS

router = APIRouter()


@router.post("/actions/evaluate", response_model=PolicyDecision)
def evaluate_action(body: ActionEvaluateRequest) -> PolicyDecision:
    """Evaluate an action against the policy engine."""
    from app.main import policy_engine

    decision = policy_engine.evaluate(body)

    # Record decision event in the run if it exists
    run = RUNS.get(body.run_id)
    if run is not None:
        run.events.append({
            "type": "policy_decision",
            "timestamp": datetime.utcnow().isoformat(),
            "action_type": body.action_type,
            "parameters": body.parameters,
            "decision": decision.decision,
            "reason": decision.reason,
        })

    return decision
