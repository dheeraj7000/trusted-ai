"""Benchmark runner that executes scenarios and produces a scorecard."""
import time
from typing import Any

from app.agent.runner import AgentRunner
from app.benchmarks.scenarios import SCENARIOS, Scenario
from app.benchmarks.scorecard import ScenarioResult, Scorecard, compute_scorecard
from app.evidence.hashing import (
    compute_provenance_root,
    compute_receipt_root,
    compute_state_root,
    compute_trace_root,
)
from app.evidence.receipt import build_receipt, verify_receipt
from app.evidence.signing import KeyManager
from app.fixtures import DEFAULT_POLICY
from app.models import PolicyConfig
from app.policy.engine import PolicyEngine


class BenchmarkRunner:
    """Runs benchmark scenarios and collects results."""

    def __init__(self, policy_engine: PolicyEngine, key_manager: KeyManager) -> None:
        self.policy_engine = policy_engine
        self.key_manager = key_manager
        self.policy = DEFAULT_POLICY

    def run_scenario(self, scenario: Scenario) -> ScenarioResult:
        """Execute a single scenario and evaluate against expectations."""
        start = time.monotonic()

        # Run the scenario through the agent runner
        agent_runner = AgentRunner(
            policy_engine=self.policy_engine,
            model_provider="benchmark",
            model_id="benchmark-v1",
        )
        run_state = agent_runner.run({
            "agent_id": "benchmark-agent",
            "actions": scenario.actions,
        })

        # Collect actual decisions from events
        actual_decisions: list[str] = []
        for event in run_state.events:
            if event.get("type") == "policy_decision":
                actual_decisions.append(event["decision"])

        # Check policy adherence: do actual decisions match expected?
        policy_adherence = actual_decisions == list(scenario.expected_decisions)

        # Count unauthorized actions (actions that were ALLOW when expected BLOCK)
        unauthorized_actions = 0
        for actual, expected in zip(actual_decisions, scenario.expected_decisions):
            if expected == "BLOCK" and actual == "ALLOW":
                unauthorized_actions += 1

        # Build receipt
        receipt = build_receipt(
            run_state=run_state,
            policy=self.policy,
            key_manager=self.key_manager,
        )

        # Apply tamper step if present
        if scenario.tamper_step:
            receipt = self._apply_tamper(receipt, run_state, scenario.tamper_step)

        # Verify receipt
        verification = verify_receipt(receipt, self.key_manager)
        actual_verification = "VALID" if verification["valid"] else "INVALID"
        evidence_integrity = actual_verification == scenario.expected_verification

        elapsed_ms = (time.monotonic() - start) * 1000

        passed = policy_adherence and evidence_integrity and unauthorized_actions == 0

        details_parts: list[str] = []
        if not policy_adherence:
            details_parts.append(
                f"Decision mismatch: expected {scenario.expected_decisions}, got {actual_decisions}"
            )
        if not evidence_integrity:
            details_parts.append(
                f"Verification mismatch: expected {scenario.expected_verification}, got {actual_verification}"
            )
        if unauthorized_actions > 0:
            details_parts.append(f"Unauthorized actions: {unauthorized_actions}")

        return ScenarioResult(
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            passed=passed,
            policy_adherence=policy_adherence,
            unauthorized_actions=unauthorized_actions,
            evidence_integrity=evidence_integrity,
            latency_ms=round(elapsed_ms, 2),
            details="; ".join(details_parts) if details_parts else "OK",
        )

    def run_all(self) -> Scorecard:
        """Run all benchmark scenarios and return a scorecard."""
        results = [self.run_scenario(s) for s in SCENARIOS]
        return compute_scorecard(results)

    def _apply_tamper(self, receipt, run_state, tamper_step: dict[str, Any]):
        """Apply a tampering operation to a receipt to test integrity detection."""
        tamper_type = tamper_step.get("type")

        if tamper_type == "modify_source":
            # Modify a source object in events, then rebuild provenance root
            # but keep the receipt's other roots the same -> receipt_root mismatch
            for event in run_state.events:
                if event.get("type") == "action_requested":
                    event[tamper_step["field"]] = tamper_step["new_value"]
                    break
            # Recompute provenance root with tampered data
            source_objects = [
                e for e in run_state.events
                if e.get("type") in ("action_requested", "tool_executed")
            ]
            new_provenance = compute_provenance_root(source_objects) if source_objects else receipt.provenance_root
            receipt.provenance_root = new_provenance
            # Receipt root no longer matches signature
            return receipt

        elif tamper_type == "drop_event":
            # Drop an event from trace, recompute trace_root
            event_index = tamper_step.get("event_index", 0)
            if event_index < len(run_state.events):
                run_state.events.pop(event_index)
            trace_events = list(run_state.events)
            new_trace_root = compute_trace_root(trace_events) if trace_events else receipt.trace_root
            receipt.trace_root = new_trace_root
            return receipt

        elif tamper_type == "modify_state":
            # Modify a field on the receipt itself (e.g., container_image_digest)
            field = tamper_step.get("field")
            new_value = tamper_step.get("new_value")
            if hasattr(receipt, field):
                setattr(receipt, field, new_value)
            # Recompute state_root with modified value -> receipt_root mismatch
            from app.evidence.state_manifest import build_state_manifest
            state_manifest = build_state_manifest(run_state, self.policy)
            state_manifest["image_digest"] = new_value
            new_state_root = compute_state_root(state_manifest)
            receipt.state_root = new_state_root
            return receipt

        elif tamper_type == "remove_policy_events":
            # Remove all policy_decision events, recompute trace
            run_state.events = [
                e for e in run_state.events if e.get("type") != "policy_decision"
            ]
            trace_events = list(run_state.events)
            new_trace_root = compute_trace_root(trace_events) if trace_events else receipt.trace_root
            receipt.trace_root = new_trace_root
            return receipt

        return receipt
