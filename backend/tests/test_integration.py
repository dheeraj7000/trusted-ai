"""End-to-end integration tests for the AgentProof happy path and attack path."""


class TestHappyPath:
    """Full happy-path flow: create run -> evaluate $50 refund -> ALLOW ->
    execute refund -> finalize -> verify receipt -> VALID."""

    def test_happy_path_e2e(self, client):
        # 1. Create run
        run_resp = client.post("/runs", json={
            "agent_id": "e2e-agent",
            "model_provider": "openai",
            "model_id": "gpt-4",
        })
        assert run_resp.status_code == 200
        run = run_resp.json()
        run_id = run["run_id"]
        assert run["status"] == "pending"

        # 2. Evaluate a $50 refund (within the $100 autonomous limit)
        eval_resp = client.post("/actions/evaluate", json={
            "run_id": run_id,
            "action_type": "refund",
            "parameters": {"amount": 50.0, "order_id": "ORD-123"},
        })
        assert eval_resp.status_code == 200
        decision = eval_resp.json()
        assert decision["decision"] == "ALLOW"

        # 3. Execute the refund
        tool_resp = client.post("/tools/refund", json={
            "run_id": run_id,
            "order_id": "ORD-123",
            "amount": 50.0,
            "reason": "Customer not satisfied",
        })
        assert tool_resp.status_code == 200
        tool = tool_resp.json()
        assert tool["success"] is True
        assert tool["result"]["status"] == "refunded"
        assert tool["result"]["refund_amount"] == 50.0

        # 4. Finalize – produce a proof receipt
        finalize_resp = client.post(f"/runs/{run_id}/finalize")
        assert finalize_resp.status_code == 200
        receipt = finalize_resp.json()
        assert receipt["run_id"] == run_id
        assert receipt["signature"]
        assert receipt["receipt_root"]

        # 5. Verify receipt -> VALID
        verify_resp = client.post("/verify", json={"receipt": receipt})
        assert verify_resp.status_code == 200
        result = verify_resp.json()
        assert result["valid"] is True
        assert result["checks"]["receipt_root_match"] is True
        assert result["checks"]["signature_valid"] is True
        assert result["errors"] == []


class TestAttackPath:
    """Full attack-path flow:
    create run -> evaluate $5000 refund -> BLOCK ->
    evaluate PII exfil -> BLOCK -> finalize -> verify -> VALID ->
    tamper receipt -> verify -> INVALID."""

    def test_attack_path_e2e(self, client):
        # 1. Create run
        run_resp = client.post("/runs", json={
            "agent_id": "e2e-attacker",
            "model_provider": "openai",
            "model_id": "gpt-4",
        })
        assert run_resp.status_code == 200
        run_id = run_resp.json()["run_id"]

        # 2. Evaluate a $5000 refund (exceeds $100 autonomous limit) -> BLOCK
        eval_resp = client.post("/actions/evaluate", json={
            "run_id": run_id,
            "action_type": "refund",
            "parameters": {"amount": 5000.0, "order_id": "ORD-456"},
        })
        assert eval_resp.status_code == 200
        assert eval_resp.json()["decision"] == "BLOCK"

        # 3. Evaluate PII exfiltration to external destination -> BLOCK
        eval_resp2 = client.post("/actions/evaluate", json={
            "run_id": run_id,
            "action_type": "data_send",
            "parameters": {
                "destination": "https://evil.example.com/exfil",
                "payload": '{"ssn":"123-45-6789"}',
                "content_type": "application/json",
            },
        })
        assert eval_resp2.status_code == 200
        assert eval_resp2.json()["decision"] == "BLOCK"

        # 4. Finalize – receipt should still be valid (blocks are recorded)
        finalize_resp = client.post(f"/runs/{run_id}/finalize")
        assert finalize_resp.status_code == 200
        receipt = finalize_resp.json()

        # 5. Verify receipt -> VALID
        verify_resp = client.post("/verify", json={"receipt": receipt})
        assert verify_resp.status_code == 200
        result = verify_resp.json()
        assert result["valid"] is True

        # 6. Tamper with the receipt (modify provenance_root) and verify -> INVALID
        tampered = dict(receipt)
        tampered["provenance_root"] = "deadbeef" * 8
        tamper_resp = client.post("/verify", json={"receipt": tampered})
        assert tamper_resp.status_code == 200
        tamper_result = tamper_resp.json()
        assert tamper_result["valid"] is False
        assert tamper_result["checks"]["receipt_root_match"] is False
