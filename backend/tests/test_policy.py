"""Tests for the PolicyEngine."""

from app.models import ActionEvaluateRequest


class TestRefundPolicy:
    """Tests for the refund policy evaluation."""

    def test_refund_under_limit_allowed(self, engine):
        action = ActionEvaluateRequest(
            run_id="test-run-1",
            action_type="refund",
            parameters={"amount": 50.0, "order_id": "ORD-123"},
        )
        decision = engine.evaluate(action)
        assert decision.decision == "ALLOW"
        assert decision.action_type == "refund"
        assert decision.policy_version == "demo-v1"

    def test_refund_at_limit_allowed(self, engine):
        action = ActionEvaluateRequest(
            run_id="test-run-2",
            action_type="refund",
            parameters={"amount": 100.0, "order_id": "ORD-123"},
        )
        decision = engine.evaluate(action)
        assert decision.decision == "ALLOW"

    def test_refund_over_limit_blocked(self, engine):
        action = ActionEvaluateRequest(
            run_id="test-run-3",
            action_type="refund",
            parameters={"amount": 100.01, "order_id": "ORD-456"},
        )
        decision = engine.evaluate(action)
        assert decision.decision == "BLOCK"
        assert "exceeds" in decision.reason.lower() or "limit" in decision.reason.lower()

    def test_refund_large_amount_blocked(self, engine):
        action = ActionEvaluateRequest(
            run_id="test-run-4",
            action_type="refund",
            parameters={"amount": 5000.0, "order_id": "ORD-456"},
        )
        decision = engine.evaluate(action)
        assert decision.decision == "BLOCK"


class TestDataSendPolicy:
    """Tests for the data_send policy evaluation."""

    def test_allowed_destination_clean_data(self, engine):
        action = ActionEvaluateRequest(
            run_id="test-run-5",
            action_type="data_send",
            parameters={
                "destination": "internal://case-system",
                "payload": "Order ORD-123 refund processed successfully.",
            },
        )
        decision = engine.evaluate(action)
        assert decision.decision == "ALLOW"
        assert decision.action_type == "data_send"

    def test_unknown_destination_blocked(self, engine):
        action = ActionEvaluateRequest(
            run_id="test-run-6",
            action_type="data_send",
            parameters={
                "destination": "https://external-api.example.com",
                "payload": "Some data",
            },
        )
        decision = engine.evaluate(action)
        assert decision.decision == "BLOCK"
        assert "not in allowed" in decision.reason.lower() or "destination" in decision.reason.lower()

    def test_sensitive_data_ssn_blocked(self, engine):
        action = ActionEvaluateRequest(
            run_id="test-run-7",
            action_type="data_send",
            parameters={
                "destination": "internal://case-system",
                "payload": "Customer SSN: 123-45-6789",
            },
        )
        decision = engine.evaluate(action)
        assert decision.decision == "BLOCK"
        assert "sensitive" in decision.reason.lower()

    def test_sensitive_data_email_blocked(self, engine):
        action = ActionEvaluateRequest(
            run_id="test-run-8",
            action_type="data_send",
            parameters={
                "destination": "internal://case-system",
                "payload": "Contact: alice@example.com",
            },
        )
        decision = engine.evaluate(action)
        assert decision.decision == "BLOCK"

    def test_sensitive_data_payment_token_blocked(self, engine):
        action = ActionEvaluateRequest(
            run_id="test-run-9",
            action_type="data_send",
            parameters={
                "destination": "internal://case-system",
                "payload": "Token: tok_alice_visa_4242",
            },
        )
        decision = engine.evaluate(action)
        assert decision.decision == "BLOCK"
