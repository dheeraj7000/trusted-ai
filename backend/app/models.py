"""Pydantic models for AgentProof."""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class PolicyConfig(BaseModel):
    policy_version: str
    refund_autonomous_limit: float
    human_approval_above: float
    allowed_data_destinations: list[str]
    sensitive_fields: list[str]


class Customer(BaseModel):
    id: str
    name: str
    email: str
    ssn: str
    payment_token: str


class Order(BaseModel):
    id: str
    customer_id: str
    amount: float
    status: str
    items: list[str]


class RefundRequest(BaseModel):
    run_id: str
    order_id: str
    amount: float
    reason: str


class DataSendRequest(BaseModel):
    run_id: str
    destination: str
    payload: str
    content_type: str


class ActionEvaluateRequest(BaseModel):
    run_id: str
    action_type: Literal["refund", "data_send"]
    parameters: dict[str, Any]


class PolicyDecision(BaseModel):
    action_type: str
    decision: Literal["ALLOW", "BLOCK"]
    reason: str
    policy_version: str
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


class RunCreate(BaseModel):
    agent_id: str
    model_provider: str
    model_id: str
    scenario: Optional[dict[str, Any]] = None


class RunState(BaseModel):
    run_id: str
    agent_id: str
    model_provider: str
    model_id: str
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    events: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class ToolResult(BaseModel):
    tool: str
    success: bool
    result: dict[str, Any]
    blocked: bool = False
    reason: Optional[str] = None


class ProofReceipt(BaseModel):
    receipt_version: str
    run_id: str
    timestamp: datetime
    agent_id: str
    agent_version: str
    model_provider: str
    model_id: str
    policy_version: str
    container_image_digest: str
    sbom_digest: str
    cbom_digest: str
    provenance_root: str
    trace_root: str
    state_root: str
    benchmark_id: Optional[str] = None
    benchmark_score: Optional[float] = None
    receipt_root: str
    signature: str
    key_id: str
