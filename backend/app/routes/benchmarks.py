"""Benchmark endpoints for running scenarios and viewing results."""
from fastapi import APIRouter

from app.benchmarks.runner import BenchmarkRunner
from app.benchmarks.scenarios import SCENARIOS
from app.benchmarks.scorecard import Scorecard
from app.fixtures import DEFAULT_POLICY
from app.key_manager import get_key_manager
from app.policy.engine import PolicyEngine

router = APIRouter(prefix="/benchmarks", tags=["benchmarks"])


@router.post("/run", response_model=Scorecard)
def run_benchmarks() -> Scorecard:
    """Run all benchmark scenarios and return the scorecard."""
    km = get_key_manager()
    engine = PolicyEngine(DEFAULT_POLICY)
    runner = BenchmarkRunner(policy_engine=engine, key_manager=km)
    return runner.run_all()


@router.get("/scenarios")
def list_scenarios() -> list[dict[str, str]]:
    """Return scenario names and descriptions for the frontend."""
    return [
        {"id": s.id, "name": s.name, "description": s.description}
        for s in SCENARIOS
    ]
