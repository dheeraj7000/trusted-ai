"""Tests for full receipt build and verify flow."""
from datetime import datetime

from app.evidence.receipt import build_receipt, verify_receipt
from app.evidence.signing import KeyManager
from app.models import PolicyConfig, RunState


def _make_run_state() -> RunState:
    """Create a completed run state with events for testing."""
    run = RunState(
        run_id="test-run-verify",
        agent_id="test-agent",
        model_provider="demo",
        model_id="mock-v1",
        status="completed",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        completed_at=datetime(2024, 1, 1, 12, 0, 5),
        events=[
            {
                "type": "action_requested",
                "timestamp": "2024-01-01T12:00:01",
                "action_type": "refund",
                "parameters": {"amount": 50.0, "order_id": "ORD-123"},
            },
            {
                "type": "policy_decision",
                "timestamp": "2024-01-01T12:00:02",
                "action_type": "refund",
                "decision": "ALLOW",
                "reason": "Within limit",
            },
            {
                "type": "tool_executed",
                "timestamp": "2024-01-01T12:00:03",
                "action_type": "refund",
                "result": {"order_id": "ORD-123", "refund_amount": 50.0, "status": "refunded"},
            },
        ],
    )
    return run


def _make_policy() -> PolicyConfig:
    return PolicyConfig(
        policy_version="demo-v1",
        refund_autonomous_limit=100,
        human_approval_above=100,
        allowed_data_destinations=["internal://case-system"],
        sensitive_fields=["ssn"],
    )


class TestBuildAndVerifyReceipt:
    def test_build_receipt_populates_all_fields(self):
        km = KeyManager.generate_dev_key()
        run = _make_run_state()
        policy = _make_policy()

        receipt = build_receipt(run, policy, km)
        assert receipt.run_id == "test-run-verify"
        assert receipt.receipt_version == "0.1.0"
        assert receipt.agent_version == "0.1.0"
        assert receipt.provenance_root
        assert receipt.trace_root
        assert receipt.state_root
        assert receipt.receipt_root
        assert receipt.signature
        assert receipt.key_id == km.key_id
        assert receipt.policy_version == "demo-v1"
        assert receipt.container_image_digest
        assert receipt.sbom_digest
        assert receipt.cbom_digest

    def test_valid_receipt_verifies(self):
        km = KeyManager.generate_dev_key()
        run = _make_run_state()
        policy = _make_policy()

        receipt = build_receipt(run, policy, km)
        result = verify_receipt(receipt, km)

        assert result["valid"] is True
        assert result["checks"]["signature_valid"] is True
        assert result["checks"]["receipt_root_match"] is True
        assert result["errors"] == []

    def test_tampered_provenance_root_fails(self):
        km = KeyManager.generate_dev_key()
        run = _make_run_state()
        policy = _make_policy()

        receipt = build_receipt(run, policy, km)
        receipt.provenance_root = "0" * 64  # tamper

        result = verify_receipt(receipt, km)
        assert result["valid"] is False
        assert result["checks"]["receipt_root_match"] is False

    def test_tampered_signature_fails(self):
        km = KeyManager.generate_dev_key()
        run = _make_run_state()
        policy = _make_policy()

        receipt = build_receipt(run, policy, km)
        # Build another receipt to get a different valid signature
        km2 = KeyManager.generate_dev_key()
        receipt2 = build_receipt(run, policy, km2)

        # Use wrong signature
        receipt.signature = receipt2.signature

        result = verify_receipt(receipt, km)
        assert result["valid"] is False
        assert result["checks"]["signature_valid"] is False

    def test_wrong_key_fails_verification(self):
        km = KeyManager.generate_dev_key()
        km_other = KeyManager.generate_dev_key()
        run = _make_run_state()
        policy = _make_policy()

        receipt = build_receipt(run, policy, km)
        result = verify_receipt(receipt, km_other)

        assert result["valid"] is False
        assert result["checks"]["signature_valid"] is False


class TestReceiptIntegrationAPI:
    """Test receipt endpoints via the API client."""

    def test_finalize_and_verify(self, client):
        # Create a run with a scenario
        run_resp = client.post("/runs", json={
            "agent_id": "test-agent",
            "model_provider": "demo",
            "model_id": "mock-v1",
            "scenario": {
                "agent_id": "test-agent",
                "actions": [
                    {
                        "action_type": "refund",
                        "parameters": {"amount": 50.0, "order_id": "ORD-123", "reason": "test"},
                    },
                ],
            },
        })
        assert run_resp.status_code == 200
        run_id = run_resp.json()["run_id"]

        # Finalize
        finalize_resp = client.post(f"/runs/{run_id}/finalize")
        assert finalize_resp.status_code == 200
        receipt_data = finalize_resp.json()
        assert receipt_data["run_id"] == run_id
        assert receipt_data["receipt_root"]
        assert receipt_data["signature"]

        # Verify by receipt_id
        verify_resp = client.post("/verify", json={"receipt_id": run_id})
        assert verify_resp.status_code == 200
        result = verify_resp.json()
        assert result["valid"] is True

    def test_get_receipt(self, client):
        run_resp = client.post("/runs", json={
            "agent_id": "test-agent",
            "model_provider": "demo",
            "model_id": "mock-v1",
            "scenario": {
                "agent_id": "test-agent",
                "actions": [
                    {
                        "action_type": "refund",
                        "parameters": {"amount": 50.0, "order_id": "ORD-123", "reason": "test"},
                    },
                ],
            },
        })
        run_id = run_resp.json()["run_id"]

        client.post(f"/runs/{run_id}/finalize")

        get_resp = client.get(f"/receipts/{run_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["run_id"] == run_id

    def test_timeline_endpoint(self, client):
        run_resp = client.post("/runs", json={
            "agent_id": "test-agent",
            "model_provider": "demo",
            "model_id": "mock-v1",
            "scenario": {
                "agent_id": "test-agent",
                "actions": [
                    {
                        "action_type": "refund",
                        "parameters": {"amount": 50.0, "order_id": "ORD-123", "reason": "test"},
                    },
                ],
            },
        })
        run_id = run_resp.json()["run_id"]

        timeline_resp = client.get(f"/runs/{run_id}/timeline")
        assert timeline_resp.status_code == 200
        timeline = timeline_resp.json()
        assert len(timeline) > 0
        assert timeline[0]["sequence"] == 1
        assert "type" in timeline[0]
        assert "summary" in timeline[0]
