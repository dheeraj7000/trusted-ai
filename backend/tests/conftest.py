"""Shared pytest fixtures for AgentProof tests."""

import pytest
from fastapi.testclient import TestClient

from app.fixtures import DEFAULT_POLICY
from app.main import app
from app.models import PolicyConfig
from app.policy.engine import PolicyEngine
from app.routes.runs import RUNS


@pytest.fixture()
def client():
    """Provide a TestClient for the FastAPI app, clearing runs between tests."""
    RUNS.clear()
    with TestClient(app) as c:
        yield c
    RUNS.clear()


@pytest.fixture()
def engine():
    """Provide a fresh PolicyEngine with the default policy."""
    return PolicyEngine(DEFAULT_POLICY)


@pytest.fixture()
def policy_config():
    """Provide the default PolicyConfig."""
    return DEFAULT_POLICY
