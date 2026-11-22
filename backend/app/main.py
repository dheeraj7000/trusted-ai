"""AgentProof FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.fixtures import DEFAULT_POLICY
from app.policy.engine import PolicyEngine
from app.routes import actions, benchmarks, runs, tools
from app.routes import receipts, verify
from app.telemetry.tracing import setup_tracing

app = FastAPI(title="AgentProof", version="0.1.0")

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
