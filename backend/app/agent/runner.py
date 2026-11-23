"""Mock agent runner for demo scenarios."""
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from app.models import (
    ActionEvaluateRequest,
    DataSendRequest,
    RefundRequest,
    RunState,
)
from app.policy.engine import PolicyEngine
from app.telemetry.tracing import create_run_span, get_tracer, record_event
from app.tools.data_send import execute_data_send
from app.tools.refund import execute_refund

tracer = get_tracer()


class AgentRunner:
    """Runs demo agent scenarios through the policy engine."""

    def __init__(
        self,
        policy_engine: PolicyEngine,
        model_provider: str = "demo",
        model_id: str = "mock-v1",
    ) -> None:
        self.policy_engine = policy_engine
        self.model_provider = model_provider
        self.model_id = model_id

    def run(self, scenario: dict) -> RunState:
        """Execute a scenario, processing each action through the policy engine."""
        run_state = RunState(
            run_id=str(uuid4()),
            agent_id=scenario.get("agent_id", "demo-agent"),
            model_provider=self.model_provider,
            model_id=self.model_id,
            status="running",
        )

        actions = scenario.get("actions", [])
        with create_run_span(run_state.run_id) as root_span:
            for action_def in actions:
                action_type = action_def.get("action_type")
                parameters = action_def.get("parameters", {})

                # Record action requested
                run_state.events.append({
                    "type": "action_requested",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action_type": action_type,
                    "parameters": parameters,
                })
                record_event(root_span, "action_requested", {"action_type": action_type})

                # Evaluate through policy engine
                eval_request = ActionEvaluateRequest(
                    run_id=run_state.run_id,
                    action_type=action_type,
                    parameters=parameters,
                )
                with tracer.start_as_current_span(
                    "policy.evaluate",
                    attributes={"action_type": action_type},
                ) as eval_span:
                    decision = self.policy_engine.evaluate(eval_request)
                    eval_span.set_attribute("decision", decision.decision)

                run_state.events.append({
                    "type": "policy_decision",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action_type": action_type,
                    "decision": decision.decision,
                    "reason": decision.reason,
                })

                # Execute or block based on decision
                if decision.decision == "ALLOW":
                    with tracer.start_as_current_span(
                        f"tool.{action_type}",
                        attributes={"action_type": action_type},
                    ) as tool_span:
                        result = self._execute_tool(action_type, parameters, run_state.run_id)
                        tool_span.set_attribute("success", result.get("success", False) if isinstance(result, dict) else False)

                    run_state.events.append({
                        "type": "tool_executed",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "action_type": action_type,
                        "result": result,
                    })
                else:
                    run_state.events.append({
                        "type": "tool_blocked",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "action_type": action_type,
                        "reason": decision.reason,
                    })

        run_state.status = "completed"
        run_state.completed_at = datetime.now(timezone.utc)
        return run_state

    def _execute_tool(
        self, action_type: str, parameters: dict, run_id: str
    ) -> dict:
        """Execute the appropriate tool for the action type."""
        if action_type == "refund":
            request = RefundRequest(
                run_id=run_id,
                order_id=parameters.get("order_id", ""),
                amount=parameters.get("amount", 0),
                reason=parameters.get("reason", ""),
            )
            tool_result = execute_refund(request)
            return tool_result.model_dump()
        elif action_type == "data_send":
            request = DataSendRequest(
                run_id=run_id,
                destination=parameters.get("destination", ""),
                payload=parameters.get("payload", ""),
                content_type=parameters.get("content_type", "text/plain"),
            )
            tool_result = execute_data_send(request)
            return tool_result.model_dump()
        else:
            return {"error": f"Unknown tool: {action_type}"}
