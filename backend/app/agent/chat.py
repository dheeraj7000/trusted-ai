"""Agent chat loop with Bedrock + policy engine integration."""
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from app.agent.bedrock import BedrockAgent
from app.evidence.receipt import build_receipt
from app.fixtures import DEFAULT_POLICY
from app.key_manager import get_key_manager
from app.models import (
    ActionEvaluateRequest,
    ChatResponse,
    DataSendRequest,
    PolicyDecision,
    ProofReceipt,
    RefundRequest,
    RunState,
)
from app.policy.engine import PolicyEngine
from app.tools.data_send import execute_data_send
from app.tools.refund import execute_refund

logger = logging.getLogger(__name__)

# Module-level Bedrock agent (lazy singleton)
_bedrock_agent: BedrockAgent | None = None


def _get_bedrock_agent() -> BedrockAgent:
    """Return the shared BedrockAgent, creating one on first call."""
    global _bedrock_agent
    if _bedrock_agent is None:
        _bedrock_agent = BedrockAgent()
    return _bedrock_agent


def run_agent_chat(message: str, policy_engine: PolicyEngine) -> ChatResponse:
    """Run a full agent chat loop for a user message.

    If Bedrock is available, uses Claude via Converse API with tool use.
    Otherwise falls back to mock keyword-based scenario execution.
    """
    bedrock = _get_bedrock_agent()

    if bedrock.available:
        try:
            return _run_bedrock_chat(message, policy_engine, bedrock)
        except RuntimeError:
            logger.warning("Bedrock chat failed, falling back to mock")

    return _run_mock_chat(message, policy_engine)


def _run_bedrock_chat(
    message: str,
    policy_engine: PolicyEngine,
    bedrock: BedrockAgent,
) -> ChatResponse:
    """Run agent loop using Bedrock Converse API."""
    run_state = RunState(
        run_id=str(uuid4()),
        agent_id="bedrock-agent",
        model_provider="aws-bedrock",
        model_id="claude-3-haiku",
        status="running",
    )

    decisions: list[PolicyDecision] = []
    messages: list[dict[str, Any]] = [
        {"role": "user", "content": [{"text": message}]}
    ]
    reply_text = ""

    # Agentic loop: iterate until model stops requesting tools
    max_iterations = 10
    for _ in range(max_iterations):
        response = bedrock.converse(messages)
        stop_reason = response.get("stopReason", "end_turn")
        output = response.get("output", {})
        output_message = output.get("message", {})
        content_blocks = output_message.get("content", [])

        # Append assistant message to conversation
        messages.append({"role": "assistant", "content": content_blocks})

        if stop_reason == "tool_use":
            tool_results: list[dict[str, Any]] = []
            for block in content_blocks:
                if "toolUse" in block:
                    tool_use = block["toolUse"]
                    tool_name = tool_use["name"]
                    tool_input = tool_use.get("input", {})
                    tool_use_id = tool_use["toolUseId"]

                    # Record action requested
                    run_state.events.append({
                        "type": "action_requested",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "action_type": tool_name,
                        "parameters": tool_input,
                    })

                    # Evaluate through policy engine
                    eval_request = ActionEvaluateRequest(
                        run_id=run_state.run_id,
                        action_type=tool_name,
                        parameters=tool_input,
                    )
                    decision = policy_engine.evaluate(eval_request)
                    decisions.append(decision)

                    run_state.events.append({
                        "type": "policy_decision",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "action_type": tool_name,
                        "decision": decision.decision,
                        "reason": decision.reason,
                    })

                    # Execute or block
                    if decision.decision == "ALLOW":
                        result = _execute_tool(
                            tool_name, tool_input, run_state.run_id
                        )
                        run_state.events.append({
                            "type": "tool_executed",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "action_type": tool_name,
                            "result": result,
                        })
                        tool_results.append({
                            "toolResult": {
                                "toolUseId": tool_use_id,
                                "content": [{"json": result}],
                            }
                        })
                    else:
                        run_state.events.append({
                            "type": "tool_blocked",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "action_type": tool_name,
                            "reason": decision.reason,
                        })
                        tool_results.append({
                            "toolResult": {
                                "toolUseId": tool_use_id,
                                "content": [
                                    {
                                        "json": {
                                            "error": "BLOCKED",
                                            "reason": decision.reason,
                                        }
                                    }
                                ],
                                "status": "error",
                            }
                        })

            # Feed tool results back to the model
            messages.append({"role": "user", "content": tool_results})
        else:
            # end_turn — extract text reply
            for block in content_blocks:
                if "text" in block:
                    reply_text += block["text"]
            break

    # Finalize
    run_state.status = "completed"
    run_state.completed_at = datetime.now(timezone.utc)

    # Build receipt
    receipt = _build_receipt_safe(run_state)

    return ChatResponse(
        reply=reply_text or "I processed your request.",
        run_id=run_state.run_id,
        events=[e for e in run_state.events],
        decisions=decisions,
        receipt=receipt,
        used_bedrock=True,
    )


def _run_mock_chat(message: str, policy_engine: PolicyEngine) -> ChatResponse:
    """Fallback mock chat using keyword matching and AgentRunner."""
    from app.agent.runner import AgentRunner

    actions = _parse_mock_actions(message)
    scenario = {
        "agent_id": "mock-agent",
        "actions": actions,
    }

    runner = AgentRunner(
        policy_engine=policy_engine,
        model_provider="mock",
        model_id="keyword-v1",
    )
    run_state = runner.run(scenario)

    # Collect decisions from events
    decisions: list[PolicyDecision] = []
    for event in run_state.events:
        if event.get("type") == "policy_decision":
            decisions.append(
                PolicyDecision(
                    action_type=event["action_type"],
                    decision=event["decision"],
                    reason=event["reason"],
                    policy_version=DEFAULT_POLICY.policy_version,
                )
            )

    # Build reply text
    reply = _build_mock_reply(message, decisions)

    # Build receipt
    receipt = _build_receipt_safe(run_state)

    return ChatResponse(
        reply=reply,
        run_id=run_state.run_id,
        events=[e for e in run_state.events],
        decisions=decisions,
        receipt=receipt,
        used_bedrock=False,
    )


def _parse_mock_actions(message: str) -> list[dict[str, Any]]:
    """Parse user message into mock scenario actions via keyword matching."""
    actions: list[dict[str, Any]] = []
    msg_lower = message.lower()

    # Detect refund requests
    amount_match = re.search(r"\$?([\d,]+(?:\.\d{2})?)", message)
    if "refund" in msg_lower and amount_match:
        amount_str = amount_match.group(1).replace(",", "")
        amount = float(amount_str)
        # Try to find an order ID in the message
        order_match = re.search(r"(ORD-\d+)", message, re.IGNORECASE)
        order_id = order_match.group(1).upper() if order_match else "ORD-123"
        actions.append({
            "action_type": "refund",
            "parameters": {
                "order_id": order_id,
                "amount": amount,
                "reason": "Customer requested refund via chat",
            },
        })
    elif "refund" in msg_lower:
        # Refund without amount — use a small default
        actions.append({
            "action_type": "refund",
            "parameters": {
                "order_id": "ORD-123",
                "amount": 79.99,
                "reason": "Customer requested refund via chat",
            },
        })

    # Detect data send / exfiltration attempts
    if "send" in msg_lower and (
        "ssn" in msg_lower or "data" in msg_lower or "evil" in msg_lower
    ):
        destination = "external://evil.com"
        if "internal" in msg_lower or "case" in msg_lower:
            destination = "internal://case-system"
        actions.append({
            "action_type": "data_send",
            "parameters": {
                "destination": destination,
                "payload": "SSN: 123-45-6789"
                if "ssn" in msg_lower
                else "customer data",
                "content_type": "text/plain",
            },
        })

    # If nothing matched, default to a simple safe refund
    if not actions:
        actions.append({
            "action_type": "refund",
            "parameters": {
                "order_id": "ORD-123",
                "amount": 79.99,
                "reason": "General customer inquiry",
            },
        })

    return actions


def _build_mock_reply(message: str, decisions: list[PolicyDecision]) -> str:
    """Generate a human-readable reply based on mock decisions."""
    parts: list[str] = []
    for d in decisions:
        if d.decision == "ALLOW":
            parts.append(f"Approved {d.action_type}: {d.reason}")
        else:
            parts.append(f"Blocked {d.action_type}: {d.reason}")

    if parts:
        return "Here's what happened with your request:\n" + "\n".join(parts)
    return "I processed your request but no actions were needed."


def _execute_tool(action_type: str, parameters: dict, run_id: str) -> dict:
    """Execute a tool and return the result dict."""
    if action_type == "refund":
        request = RefundRequest(
            run_id=run_id,
            order_id=parameters.get("order_id", ""),
            amount=parameters.get("amount", 0),
            reason=parameters.get("reason", ""),
        )
        return execute_refund(request).model_dump()
    elif action_type == "data_send":
        request = DataSendRequest(
            run_id=run_id,
            destination=parameters.get("destination", ""),
            payload=parameters.get("payload", ""),
            content_type=parameters.get("content_type", "text/plain"),
        )
        return execute_data_send(request).model_dump()
    return {"error": f"Unknown tool: {action_type}"}


def _build_receipt_safe(run_state: RunState) -> Optional[ProofReceipt]:
    """Build a receipt, returning None on failure."""
    try:
        km = get_key_manager()
        return build_receipt(run_state, DEFAULT_POLICY, km)
    except Exception as e:
        logger.warning("Failed to build receipt: %s", e)
        return None
