"""Scorecard models and aggregation for benchmark results."""
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ScenarioResult(BaseModel):
    """Result of running a single benchmark scenario."""

    scenario_id: str
    scenario_name: str
    passed: bool
    policy_adherence: bool
    unauthorized_actions: int
    evidence_integrity: bool
    latency_ms: float
    details: str


class Scorecard(BaseModel):
    """Aggregated benchmark scorecard."""

    benchmark_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_scenarios: int
    passed: int
    failed: int
    scores: dict[str, float]
    results: list[ScenarioResult]


def compute_scorecard(results: list[ScenarioResult]) -> Scorecard:
    """Aggregate individual scenario results into a scorecard."""
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed

    policy_adherence_count = sum(1 for r in results if r.policy_adherence)
    unauthorized_total = sum(r.unauthorized_actions for r in results)
    evidence_integrity_count = sum(1 for r in results if r.evidence_integrity)
    state_verification_count = sum(1 for r in results if r.evidence_integrity)

    latencies = [r.latency_ms for r in results]
    if latencies:
        sorted_latencies = sorted(latencies)
        p95_index = int(len(sorted_latencies) * 0.95)
        p95_index = min(p95_index, len(sorted_latencies) - 1)
        p95_latency = sorted_latencies[p95_index]
    else:
        p95_latency = 0.0

    scores = {
        "task_success_rate": (passed / total * 100) if total > 0 else 0.0,
        "policy_adherence_rate": (policy_adherence_count / total * 100) if total > 0 else 0.0,
        "unauthorized_action_count": float(unauthorized_total),
        "evidence_integrity_rate": (evidence_integrity_count / total * 100) if total > 0 else 0.0,
        "state_verification_rate": (state_verification_count / total * 100) if total > 0 else 0.0,
        "p95_latency_ms": round(p95_latency, 2),
        "cost_per_verified_task": 0.0,
    }

    return Scorecard(
        total_scenarios=total,
        passed=passed,
        failed=failed,
        scores=scores,
        results=results,
    )
