"""Tests for benchmark scenarios, runner, and scorecard."""
import pytest

from app.benchmarks.runner import BenchmarkRunner
from app.benchmarks.scenarios import SCENARIOS, Scenario
from app.benchmarks.scorecard import ScenarioResult, Scorecard, compute_scorecard
from app.evidence.signing import KeyManager
from app.fixtures import DEFAULT_POLICY
from app.policy.engine import PolicyEngine


@pytest.fixture()
def benchmark_runner():
    """Provide a BenchmarkRunner with a fresh key pair."""
    engine = PolicyEngine(DEFAULT_POLICY)
    km = KeyManager.generate_dev_key()
    return BenchmarkRunner(policy_engine=engine, key_manager=km)


class TestScenarioDecisions:
    """Test that each scenario produces the expected policy decisions."""

    @pytest.mark.parametrize(
        "scenario",
        SCENARIOS,
        ids=[s.id for s in SCENARIOS],
    )
    def test_scenario_policy_adherence(self, benchmark_runner, scenario):
        result = benchmark_runner.run_scenario(scenario)
        assert result.policy_adherence is True, (
            f"Scenario {scenario.id}: {result.details}"
        )

    @pytest.mark.parametrize(
        "scenario",
        [s for s in SCENARIOS if all(d == "BLOCK" for d in s.expected_decisions)],
        ids=[s.id for s in SCENARIOS if all(d == "BLOCK" for d in s.expected_decisions)],
    )
    def test_blocked_scenarios_have_no_unauthorized_actions(self, benchmark_runner, scenario):
        result = benchmark_runner.run_scenario(scenario)
        assert result.unauthorized_actions == 0, (
            f"Scenario {scenario.id} had {result.unauthorized_actions} unauthorized actions"
        )


class TestTamperedScenarios:
    """Test that tampered scenarios correctly detect integrity failures."""

    @pytest.mark.parametrize(
        "scenario",
        [s for s in SCENARIOS if s.tamper_step is not None],
        ids=[s.id for s in SCENARIOS if s.tamper_step is not None],
    )
    def test_tampered_scenario_detects_invalid(self, benchmark_runner, scenario):
        result = benchmark_runner.run_scenario(scenario)
        assert result.evidence_integrity is True, (
            f"Scenario {scenario.id} should detect tampering: {result.details}"
        )


class TestScorecardComputation:
    """Test that scorecard aggregation is correct."""

    def test_all_passing(self):
        results = [
            ScenarioResult(
                scenario_id=f"s{i}",
                scenario_name=f"Scenario {i}",
                passed=True,
                policy_adherence=True,
                unauthorized_actions=0,
                evidence_integrity=True,
                latency_ms=10.0 + i,
                details="OK",
            )
            for i in range(5)
        ]
        scorecard = compute_scorecard(results)
        assert scorecard.total_scenarios == 5
        assert scorecard.passed == 5
        assert scorecard.failed == 0
        assert scorecard.scores["task_success_rate"] == 100.0
        assert scorecard.scores["policy_adherence_rate"] == 100.0
        assert scorecard.scores["unauthorized_action_count"] == 0.0
        assert scorecard.scores["evidence_integrity_rate"] == 100.0
        assert scorecard.scores["cost_per_verified_task"] == 0.0

    def test_mixed_results(self):
        results = [
            ScenarioResult(
                scenario_id="pass",
                scenario_name="Pass",
                passed=True,
                policy_adherence=True,
                unauthorized_actions=0,
                evidence_integrity=True,
                latency_ms=5.0,
                details="OK",
            ),
            ScenarioResult(
                scenario_id="fail",
                scenario_name="Fail",
                passed=False,
                policy_adherence=False,
                unauthorized_actions=1,
                evidence_integrity=False,
                latency_ms=20.0,
                details="Decision mismatch",
            ),
        ]
        scorecard = compute_scorecard(results)
        assert scorecard.total_scenarios == 2
        assert scorecard.passed == 1
        assert scorecard.failed == 1
        assert scorecard.scores["task_success_rate"] == 50.0
        assert scorecard.scores["policy_adherence_rate"] == 50.0
        assert scorecard.scores["unauthorized_action_count"] == 1.0
        assert scorecard.scores["evidence_integrity_rate"] == 50.0

    def test_empty_results(self):
        scorecard = compute_scorecard([])
        assert scorecard.total_scenarios == 0
        assert scorecard.passed == 0
        assert scorecard.scores["task_success_rate"] == 0.0


class TestFullBenchmarkRun:
    """Test the full benchmark run produces a valid scorecard."""

    def test_run_all_produces_scorecard(self, benchmark_runner):
        scorecard = benchmark_runner.run_all()
        assert isinstance(scorecard, Scorecard)
        assert scorecard.total_scenarios == len(SCENARIOS)
        assert scorecard.total_scenarios >= 10
        assert scorecard.passed + scorecard.failed == scorecard.total_scenarios
        assert len(scorecard.results) == scorecard.total_scenarios
        assert scorecard.benchmark_id
        assert scorecard.scores["task_success_rate"] > 0

    def test_normal_refund_passes(self, benchmark_runner):
        scenario = next(s for s in SCENARIOS if s.id == "normal_refund")
        result = benchmark_runner.run_scenario(scenario)
        assert result.passed is True
        assert result.policy_adherence is True
        assert result.evidence_integrity is True
        assert result.unauthorized_actions == 0

    def test_oversized_refund_blocks(self, benchmark_runner):
        scenario = next(s for s in SCENARIOS if s.id == "oversized_refund")
        result = benchmark_runner.run_scenario(scenario)
        assert result.passed is True
        assert result.policy_adherence is True

    def test_pii_exfiltration_blocks(self, benchmark_runner):
        scenario = next(s for s in SCENARIOS if s.id == "pii_exfiltration")
        result = benchmark_runner.run_scenario(scenario)
        assert result.passed is True
        assert result.policy_adherence is True

    def test_all_scenarios_pass(self, benchmark_runner):
        scorecard = benchmark_runner.run_all()
        for r in scorecard.results:
            assert r.passed is True, f"Scenario {r.scenario_id} failed: {r.details}"


class TestBenchmarkAPI:
    """Test the benchmark API endpoints."""

    def test_post_benchmarks_run(self, client):
        resp = client.post("/benchmarks/run")
        assert resp.status_code == 200
        data = resp.json()
        assert "benchmark_id" in data
        assert "total_scenarios" in data
        assert data["total_scenarios"] >= 10
        assert "scores" in data
        assert "results" in data
        assert len(data["results"]) == data["total_scenarios"]

    def test_get_scenarios(self, client):
        resp = client.get("/benchmarks/scenarios")
        assert resp.status_code == 200
        scenarios = resp.json()
        assert len(scenarios) >= 10
        assert all("id" in s and "name" in s and "description" in s for s in scenarios)
