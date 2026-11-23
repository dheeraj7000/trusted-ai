"""Integration tests for the AgentProof API."""

import uuid


class TestHealthEndpoint:
    def test_health(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "agentproof"


class TestRunsEndpoint:
    def test_create_run(self, client):
        resp = client.post("/runs", json={
            "agent_id": "test-agent",
            "model_provider": "demo",
            "model_id": "mock-v1",
        })
        assert resp.status_code == 200
        data = resp.json()
        # Validate run_id is a valid UUID
        uuid.UUID(data["run_id"])
        assert data["agent_id"] == "test-agent"
        assert data["status"] == "pending"
        assert data["events"] == []

    def test_get_run(self, client):
        create_resp = client.post("/runs", json={
            "agent_id": "test-agent",
            "model_provider": "demo",
            "model_id": "mock-v1",
        })
        run_id = create_resp.json()["run_id"]

        resp = client.get(f"/runs/{run_id}")
        assert resp.status_code == 200
        assert resp.json()["run_id"] == run_id

    def test_get_run_not_found(self, client):
        resp = client.get("/runs/nonexistent-id")
        assert resp.status_code == 404


class TestActionsEndpoint:
    def test_evaluate_refund_allow(self, client):
        # Create a run first
        run_resp = client.post("/runs", json={
            "agent_id": "test-agent",
            "model_provider": "demo",
            "model_id": "mock-v1",
        })
        run_id = run_resp.json()["run_id"]

        resp = client.post("/actions/evaluate", json={
            "run_id": run_id,
            "action_type": "refund",
            "parameters": {"amount": 50.0, "order_id": "ORD-123"},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] == "ALLOW"
        assert data["action_type"] == "refund"

    def test_evaluate_refund_block(self, client):
        run_resp = client.post("/runs", json={
            "agent_id": "test-agent",
            "model_provider": "demo",
            "model_id": "mock-v1",
        })
        run_id = run_resp.json()["run_id"]

        resp = client.post("/actions/evaluate", json={
            "run_id": run_id,
            "action_type": "refund",
            "parameters": {"amount": 5000.0, "order_id": "ORD-456"},
        })
        assert resp.status_code == 200
        assert resp.json()["decision"] == "BLOCK"


class TestToolsEndpoint:
    def test_refund_allowed(self, client):
        # Create run, evaluate, then execute
        run_resp = client.post("/runs", json={
            "agent_id": "test-agent",
            "model_provider": "demo",
            "model_id": "mock-v1",
        })
        run_id = run_resp.json()["run_id"]

        # Evaluate first
        client.post("/actions/evaluate", json={
            "run_id": run_id,
            "action_type": "refund",
            "parameters": {"amount": 50.0, "order_id": "ORD-123"},
        })

        # Execute refund
        resp = client.post("/tools/refund", json={
            "run_id": run_id,
            "order_id": "ORD-123",
            "amount": 50.0,
            "reason": "Customer request",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["tool"] == "refund"
        assert data["success"] is True
        assert data["result"]["status"] == "refunded"
        assert data["result"]["refund_amount"] == 50.0

    def test_refund_without_evaluation_forbidden(self, client):
        run_resp = client.post("/runs", json={
            "agent_id": "test-agent",
            "model_provider": "demo",
            "model_id": "mock-v1",
        })
        run_id = run_resp.json()["run_id"]

        resp = client.post("/tools/refund", json={
            "run_id": run_id,
            "order_id": "ORD-123",
            "amount": 50.0,
            "reason": "Customer request",
        })
        assert resp.status_code == 403

    def test_data_send_allowed(self, client):
        # Create run, evaluate, then execute data-send
        run_resp = client.post("/runs", json={
            "agent_id": "test-agent",
            "model_provider": "demo",
            "model_id": "mock-v1",
        })
        run_id = run_resp.json()["run_id"]

        # Evaluate first
        client.post("/actions/evaluate", json={
            "run_id": run_id,
            "action_type": "data_send",
            "parameters": {
                "destination": "internal://case-system",
                "payload": "Order ORD-123 refund processed successfully.",
                "content_type": "text/plain",
            },
        })

        # Execute data-send
        resp = client.post("/tools/data-send", json={
            "run_id": run_id,
            "destination": "internal://case-system",
            "payload": "Order ORD-123 refund processed successfully.",
            "content_type": "text/plain",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["tool"] == "data_send"
        assert data["success"] is True
        assert data["result"]["destination"] == "internal://case-system"
        assert data["result"]["bytes_sent"] == len("Order ORD-123 refund processed successfully.")

    def test_data_send_without_evaluation_forbidden(self, client):
        run_resp = client.post("/runs", json={
            "agent_id": "test-agent",
            "model_provider": "demo",
            "model_id": "mock-v1",
        })
        run_id = run_resp.json()["run_id"]

        resp = client.post("/tools/data-send", json={
            "run_id": run_id,
            "destination": "internal://case-system",
            "payload": "some data",
            "content_type": "text/plain",
        })
        assert resp.status_code == 403

    def test_full_flow(self, client):
        """Test the complete flow: create run -> evaluate -> execute."""
        # 1. Create run
        run_resp = client.post("/runs", json={
            "agent_id": "flow-agent",
            "model_provider": "demo",
            "model_id": "mock-v1",
        })
        assert run_resp.status_code == 200
        run_id = run_resp.json()["run_id"]

        # 2. Evaluate refund
        eval_resp = client.post("/actions/evaluate", json={
            "run_id": run_id,
            "action_type": "refund",
            "parameters": {"amount": 79.99, "order_id": "ORD-123"},
        })
        assert eval_resp.json()["decision"] == "ALLOW"

        # 3. Execute refund
        tool_resp = client.post("/tools/refund", json={
            "run_id": run_id,
            "order_id": "ORD-123",
            "amount": 79.99,
            "reason": "Defective product",
        })
        assert tool_resp.status_code == 200
        assert tool_resp.json()["success"] is True

        # 4. Verify events recorded in run
        get_resp = client.get(f"/runs/{run_id}")
        events = get_resp.json()["events"]
        event_types = [e["type"] for e in events]
        assert "policy_decision" in event_types
        assert "tool_executed" in event_types
