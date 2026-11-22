"""Policy engine for evaluating agent actions."""

from datetime import datetime

from app.fixtures import CUSTOMERS
from app.models import ActionEvaluateRequest, PolicyConfig, PolicyDecision


class PolicyEngine:
    """Evaluates agent actions against configured policies."""

    def __init__(self, config: PolicyConfig) -> None:
        self.config = config

    def evaluate(self, action: ActionEvaluateRequest) -> PolicyDecision:
        """Evaluate an action against policy rules."""
        if action.action_type == "refund":
            return self._evaluate_refund(action)
        elif action.action_type == "data_send":
            return self._evaluate_data_send(action)
        else:
            return PolicyDecision(
                action_type=action.action_type,
                decision="BLOCK",
                reason=f"Unknown action type: {action.action_type}",
                policy_version=self.config.policy_version,
                evaluated_at=datetime.utcnow(),
            )

    def _evaluate_refund(self, action: ActionEvaluateRequest) -> PolicyDecision:
        """Evaluate a refund action against REFUND_LIMIT policy."""
        amount = action.parameters.get("amount", 0)

        if amount <= self.config.refund_autonomous_limit:
            return PolicyDecision(
                action_type="refund",
                decision="ALLOW",
                reason=f"Refund amount ${amount} is within autonomous limit of ${self.config.refund_autonomous_limit}",
                policy_version=self.config.policy_version,
                evaluated_at=datetime.utcnow(),
            )

        return PolicyDecision(
            action_type="refund",
            decision="BLOCK",
            reason=f"Refund amount ${amount} exceeds autonomous limit of ${self.config.refund_autonomous_limit}; requires human approval",
            policy_version=self.config.policy_version,
            evaluated_at=datetime.utcnow(),
        )

    def _evaluate_data_send(self, action: ActionEvaluateRequest) -> PolicyDecision:
        """Evaluate a data_send action against DATA_EGRESS policy."""
        destination = action.parameters.get("destination", "")
        payload = action.parameters.get("payload", "")

        # Check destination allowlist
        if destination not in self.config.allowed_data_destinations:
            return PolicyDecision(
                action_type="data_send",
                decision="BLOCK",
                reason=f"Destination '{destination}' is not in allowed destinations: {self.config.allowed_data_destinations}",
                policy_version=self.config.policy_version,
                evaluated_at=datetime.utcnow(),
            )

        # Scan payload for sensitive data values from fixtures
        sensitive_values = self._collect_sensitive_values()
        for value in sensitive_values:
            if value in payload:
                return PolicyDecision(
                    action_type="data_send",
                    decision="BLOCK",
                    reason=f"Payload contains sensitive data matching policy field restrictions",
                    policy_version=self.config.policy_version,
                    evaluated_at=datetime.utcnow(),
                )

        return PolicyDecision(
            action_type="data_send",
            decision="ALLOW",
            reason=f"Data send to '{destination}' is allowed and payload contains no sensitive data",
            policy_version=self.config.policy_version,
            evaluated_at=datetime.utcnow(),
        )

    def _collect_sensitive_values(self) -> list[str]:
        """Collect actual sensitive data values from fixtures based on configured sensitive fields."""
        field_mapping = {
            "ssn": "ssn",
            "customer_email": "email",
            "payment_token": "payment_token",
        }
        values: list[str] = []
        for customer in CUSTOMERS.values():
            for policy_field, model_attr in field_mapping.items():
                if policy_field in self.config.sensitive_fields:
                    val = getattr(customer, model_attr, None)
                    if val:
                        values.append(val)
        return values
