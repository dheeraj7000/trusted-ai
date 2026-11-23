# AgentProof

Firewall + Verifiable Flight Recorder for AI Agents

AgentProof is a tamper-evident audit system that sits between an AI agent and
the tools it calls.  Every action is evaluated against a configurable policy
engine, and every run produces a cryptographically signed proof receipt that
can be independently verified.

## Architecture

```
┌─────────────┐        ┌──────────────────────────────────────────────┐
│  Next.js UI  │◄──────►│  FastAPI Backend                              │
│  (port 3000) │        │                                              │
└─────────────┘        │  /runs           – create & inspect runs     │
                       │  /actions/evaluate – policy evaluation       │
                       │  /tools/refund    – execute refund           │
                       │  /tools/data-send – execute data send        │
                       │  /runs/{id}/finalize – build proof receipt   │
                       │  /receipts/{id}  – retrieve receipt          │
                       │  /verify         – verify receipt integrity  │
                       │  /benchmarks/*   – run & list benchmarks     │
                       └──────────────────────────────────────────────┘
```

The backend uses an in-memory store (no database required).  ECDSA P-256 keys
are generated on first use and stored in `backend/keys/` (gitignored).

## Quick Start

### Docker Compose (recommended)

```bash
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend:  http://localhost:8000

### Local Development

**Backend**

```bash
cd backend
pip install -e '.[dev]'
uvicorn app.main:app --reload --port 8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

The Next.js dev server proxies `/api/*` requests to `http://localhost:8000`
automatically.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| POST | `/runs` | Create a new agent run |
| GET | `/runs/{run_id}` | Get run details |
| GET | `/runs/{run_id}/timeline` | Get event timeline |
| POST | `/actions/evaluate` | Evaluate action against policy |
| POST | `/tools/refund` | Execute a refund (requires prior ALLOW) |
| POST | `/tools/data-send` | Execute a data send (requires prior ALLOW) |
| POST | `/runs/{run_id}/finalize` | Build and sign proof receipt |
| GET | `/receipts/{receipt_id}` | Retrieve a stored receipt |
| POST | `/verify` | Verify receipt integrity and signature |
| POST | `/benchmarks/run` | Run all benchmark scenarios |
| GET | `/benchmarks/scenarios` | List available scenarios |

## Demo Walkthrough

The frontend provides two demo paths:

### Happy Path

1. **Create run** – starts a new agent run
2. **Evaluate refund ($50)** – policy engine allows it (within $100 autonomous limit)
3. **Execute refund** – tool processes the refund
4. **Finalize** – generates a signed proof receipt
5. **Verify** – confirms the receipt is VALID

### Attack Path

1. **Create run** – starts a new agent run
2. **Evaluate refund ($5,000)** – policy engine blocks it (exceeds limit)
3. **Evaluate data send (external)** – policy engine blocks PII exfiltration
4. **Finalize** – generates a signed receipt recording the blocks
5. **Verify** – confirms the receipt is VALID
6. **Tamper** – modifying any receipt field causes verification to return INVALID

## Known Limitations

- **In-memory state is process-local.** The `RUNS` and `RECEIPTS` dicts, as
  well as the module-level `KeyManager` singleton, live in a single process.
  Running multiple uvicorn workers (e.g. `--workers 4`) will give each worker
  its own disjoint copy of state. For production multi-process or multi-node
  deployments, replace the in-memory stores with a shared backend such as
  Redis or PostgreSQL and load signing keys from a central secret store.

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

```bash
cd frontend
npm run build
```
