"""Run management endpoints."""

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.models import RunCreate, RunState

router = APIRouter()

# In-memory run storage
RUNS: dict[str, RunState] = {}


def get_run(run_id: str) -> RunState:
    """Retrieve a run by ID, raising 404 if not found."""
    run = RUNS.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return run


@router.post("/runs", response_model=RunState)
def create_run(body: RunCreate) -> RunState:
    """Create a new agent run."""
    run_id = str(uuid4())
    run = RunState(
        run_id=run_id,
        agent_id=body.agent_id,
        model_provider=body.model_provider,
        model_id=body.model_id,
        status="pending",
        created_at=datetime.utcnow(),
    )

    if body.scenario is not None:
        from app.agent.runner import AgentRunner
        from app.main import policy_engine

        runner = AgentRunner(
            policy_engine=policy_engine,
            model_provider=body.model_provider,
            model_id=body.model_id,
        )
        run = runner.run(body.scenario)
        run.agent_id = body.agent_id

    RUNS[run.run_id] = run
    return run


@router.get("/runs/{run_id}", response_model=RunState)
def read_run(run_id: str) -> RunState:
    """Get a run by ID."""
    return get_run(run_id)
