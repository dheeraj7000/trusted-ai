"""AgentProof FastAPI application."""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.fixtures import DEFAULT_POLICY
from app.policy.engine import PolicyEngine
from app.routes import actions, benchmarks, runs, tools
from app.routes import receipts, verify
from app.telemetry.tracing import setup_tracing

app = FastAPI(title="AgentProof", version="0.1.0")

# CORS middleware — configurable via AGENTPROOF_CORS_ORIGINS env var
_cors_env = os.environ.get("AGENTPROOF_CORS_ORIGINS")
_cors_origins = _cors_env.split(",") if _cors_env else ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Module-level policy engine singleton
policy_engine = PolicyEngine(DEFAULT_POLICY)

# Initialize OpenTelemetry tracing
setup_tracing()

# Include routers
app.include_router(runs.router)
app.include_router(actions.router)
app.include_router(tools.router)
app.include_router(receipts.router)
app.include_router(verify.router)
app.include_router(benchmarks.router)


@app.get("/")
def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "agentproof"}
