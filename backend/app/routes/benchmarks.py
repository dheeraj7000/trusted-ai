"""Benchmark endpoints for running scenarios and viewing results."""
from fastapi import APIRouter

from app.benchmarks.runner import BenchmarkRunner
from app.benchmarks.scenarios import SCENARIOS
from app.benchmarks.scorecard import Scorecard
from app.evidence.signing import KeyManager
from app.fixtures import DEFAULT_POLICY
from app.policy.engine import PolicyEngine

router = APIRouter(prefix="/benchmarks", tags=["benchmarks"])

# Module-level key manager for benchmarks
_benchmark_km: KeyManager | None = None


def _get_benchmark_km() -> KeyManager:
    global _benchmark_km
    if _benchmark_km is None:
        _benchmark_km = KeyManager.generate_dev_key()
    return _benchmark_km


@router.post("/run", response_model=Scorecard)
def run_benchmarks() -> Scorecard:
    """Run all benchmark scenarios and return the scorecard."""
    km = _get_benchmark_km()
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
